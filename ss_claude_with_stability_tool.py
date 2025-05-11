#!/usr/bin/env python
# coding: utf-8

# In[102]:


import json
import boto3
import base64
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
from pathlib import Path
import io


# In[103]:


# Initialize Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")


# In[104]:


def generate_and_save_image(prompt="A futuristic cityscape at sunset", filename=None, generated_images: list = []):
    """
    Generate an image using Stability SD3 model and save it to a file
    
    Args:
        prompt: Text prompt for image generation
        filename: Mandatory filename for the output image (default: timestamp-based name)
        
    Returns:
        Dictionary with image path and base64 string
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = "generated_images"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create unique filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"image-{timestamp}.png"
        
        # Make sure filename has .png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
            
        # Full path to save the image
        output_path = os.path.join(output_dir, Path(filename))
        generated_images.append(output_path)
        
        # Correct payload for SD3
        payload = {
            "prompt": prompt,
            "mode": "text-to-image",
            "output_format": "png",
            "seed": 0,
            "aspect_ratio": "1:1"
        }
        
        # Invoke SD3 model
        response = bedrock.invoke_model(
            modelId = "stability.stable-image-ultra-v1:1", 
            #modelId="stability.sd3-large-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read())
        image_base64 = result['images'][0]  # SD3 returns a list of base64-encoded images
        
        # Decode and save to file
        image_bytes = base64.b64decode(image_base64)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return generated_images, \
            {
                "success": True,
                "image_path": output_path,
                "tool_content_block": {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64
                    }
                }
            }

    except Exception as e:
        return generated_images, {"success": False, "Stability error": str(e)}


# In[105]:


def encode_image_to_base64(image_path):
    """Encode an image file to base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Error encoding image: {str(e)}")
        return None


# In[106]:


def pass_to_claude(model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0", image_data=None, image_path=None):
    """Pass an image and text to Claude 3 Sonnet for analysis."""
    prompt_text="you are trying to help this user pick the perfect graphic design image, \
                ask questions about the specifications of the image to help another \
                image generation model gauge exactly what the user wants. \
                Never ask the same question three times in a row."
    try:
        # Prepare the image data - either use provided binary data or load from path
        if image_data is None and image_path:
            image_base64 = encode_image_to_base64(image_path)
        elif image_data:
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        else:
            raise ValueError("Either image_data or image_path must be provided")
        
        # Prepare the message for Claude with the image
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt_text
                        }
                    ]
                }
            ]
        }

        # Invoke Claude 3 Sonnet
        response = bedrock.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )

        # Parse and return Claude's response
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']

    except Exception as e:
        print(f"❌ Error with Claude analysis: {str(e)}")
        return None


# In[107]:


def handle_function_calling(model_id, request, tool_config, generated_images):
    """
    Handles function calling with Claude, including the image generation tool

    Args:
        model_id: Claude model ID (e.g., "anthropic.claude-3-7-sonnet-20250219")
        request: Dictionary with messages and inferenceConfig
        tool_config: Tool configuration dictionary

    Returns:
        Dictionary with the conversation results
    """
    try:
        # Step 1: Send initial request
        response = bedrock.converse(
            modelId=model_id,
            messages=request["messages"],
            inferenceConfig=request["inferenceConfig"],
            toolConfig=tool_config
        )

        # Check if the model wants to use a tool
        content_blocks = response["output"]["message"]["content"]
        has_tool_use = any("toolUse" in block for block in content_blocks)

        if has_tool_use:
            # Find the toolUse block
            tool_use_block = next(block for block in content_blocks if "toolUse" in block)
            tool_use = tool_use_block["toolUse"]
            tool_name = tool_use["name"]
            tool_input = tool_use["input"]
            tool_use_id = tool_use["toolUseId"]

            # Step 2: Execute the tool
            if tool_name == "generate_image":
                # Extract parameters from the tool input
                prompt = tool_input.get("prompt", "A futuristic cityscape at sunset")
                filename = tool_input.get("filename")

                # Call the image generation function
                generated_images, tool_result = generate_and_save_image(prompt, filename, generated_images)
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}

            # Step 3: Send the image and prompt directly to Claude
            if tool_result.get("success"):
                claude_response = pass_to_claude(model_id, image_path=tool_result['image_path'])
            else:
                claude_response = tool_result.get("error", "Unknown error")

            return generated_images, \
            {
                "tool_call": {"name": tool_name, "input": tool_input},
                "tool_result": tool_result,
                "final_response": claude_response
            }

        else:
            # Model didn't use a tool, just return the text response
            text_response = ""
            for block in content_blocks:
                if "text" in block:
                    text_response = block["text"]
                    break

            return generated_images, {"final_response": text_response}

    except Exception as e:
        print(f"Error in function calling: {str(e)}")
        return generated_images, {"error": str(e)}


# In[108]:


def run(model_id: str, user_query: str, history: list, generated_images):
    tool_config = {
        "tools": [
            {
                "toolSpec": {
                    "name": "generate_image",
                    "description": "Generate an image based on a text prompt using Stability Image Ultra v1.1",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "Text description of the image to generate in Stable Diffusion"
                                },
                                "filename": {
                                    "type": "string",
                                    "description": "Mandatory filename for the output image (default: timestamp-based name)"
                                }
                            },
                            "required": ["prompt"]
                        }
                    }
                }
            }
        ]
    }

    # Append the new user message to the history
    history.append({
        "role": "user",
        "content": [{"text": user_query}]
    })

    # Request with full history
    request = {
        "messages": history,
        "inferenceConfig": {
            "temperature": 0.7,
            "maxTokens": 4096
        }
    }

    generated_images, result = handle_function_calling(model_id, request, tool_config, generated_images)

    if "error" in result:
        print(f"Error: {result['error']}")
        return generated_images, "error"
    else:
        if "tool_call" in result:
            print(f"Tool called: {result['tool_call']['name']}")
            print(f"Tool input: {json.dumps(result['tool_call']['input'], indent=2)}")

        print("\nClaude's response:")
        print(result["final_response"])

        # Append Claude's response to the history
        history.append({
            "role": "assistant",
            "content": [{"text": result["final_response"]}]
        })

        return generated_images, result["final_response"]


# In[109]:


# Claude 3.7 Sonnet model ID
#model_id = "anthropic.claude-3-7-sonnet-20250219-v1:0"
model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

#conv = ClaudeConversation(model_id, "You are a helpful assistant that helps refine image prompts by asking specific \
#                                        and targeted questions about image design preferences, \
#                                        to aid in generating improved images.")
history = []
generated_images = []

while True:
    user_query = input("User: ")
    if not user_query:
        break
    generated_images, result = run(model_id, user_query, history, generated_images)

for image_path in generated_images:
    if os.path.exists(image_path):
        os.remove(image_path)


# In[ ]:




