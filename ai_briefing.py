import boto3
import json
import base64
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIBriefingSystem:
    def __init__(self, region_name="us-west-2"):
        """Initialize the AI Briefing System with Bedrock client"""
        print("new ai briefing system!!!")
        try:
            self.bedrock = boto3.client("bedrock-runtime", region_name=region_name)
            # Initialize Claude model ID
            self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
            # Initialize conversation history
            self.history = []
            self.generated_images = []
            self.service_title = None
            logger.debug(f"AI Briefing System initialized with model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize AI Briefing System: {str(e)}", exc_info=True)
            raise
    
    def set_service_title(self, title: str):
        """Set the service title for context"""
        if not title:
            raise ValueError("Service title is required")
        self.service_title = title
        logger.debug(f"Service title set to: {title}")
        
        # Reset conversation when a new service title is set
        self.history = []
        
        # Add system message to history
        system_message = f"You are an AI assistant helping to gather requirements for a {title} project. Ask questions to understand the client's needs."
        self.history.append({
            "role": "assistant", 
            "content": [{"text": system_message}]
        })
        
    def get_next_question(self, user_input: str = None) -> str:
        """Get the next question to ask the user based on the conversation history."""
        if not self.service_title:
            raise ValueError("Service title must be set before getting questions")
        
        try:
            # If this is the first question and no user input yet
            if not user_input and len(self.history) <= 1:  # Only system message
                prompt = f"You are an AI assistant helping to gather requirements for a {self.service_title} project. Start with the broadest possible question to understand what kind of project the client is looking for. Focus on understanding their overall vision and goals. Keep your response concise and focused on a single question. Do not mention specific details or technical requirements yet."
                
                logger.debug(f"Generating first question with prompt: {prompt}")
                
                request = {
                    "messages": [{
                        "role": "user",
                        "content": [{"text": prompt}]
                    }],
                    "inferenceConfig": {
                        "temperature": 0.7,
                        "maxTokens": 1024
                    }
                }
                
                response = self.bedrock.converse(
                    modelId=self.model_id,
                    messages=request["messages"],
                    inferenceConfig=request["inferenceConfig"]
                )
                
                content_blocks = response["output"]["message"]["content"]
                question = ""
                for block in content_blocks:
                    if "text" in block:
                        question = block["text"].strip()
                        break
                
                # Add the assistant's question to history
                self.history.append({
                    "role": "assistant",
                    "content": [{"text": question}]
                })
                
                logger.debug(f"Generated first question: {question}")
                return question
            
            # For subsequent interactions, add user input and get next question
            if user_input:
                logger.debug(f"Processing user input: {user_input}")
                
                # Add user input to the history
                self.history.append({
                    "role": "user",
                    "content": [{"text": user_input}]
                })
                
                # Now generate the next question based on conversation so far
                next_question_prompt = f"Based on our conversation about the {self.service_title} project so far, ask the next most relevant question to gather more requirements. Reference specific details the user has shared, dig deeper into their needs, and focus on understanding their goals, audience, style preferences, specific requirements, and any constraints. Keep your response concise and focused on a single question."
                
                self.history.append({
                    "role": "user",
                    "content": [{"text": next_question_prompt}]
                })
                
                request = {
                    "messages": self.history,
                    "inferenceConfig": {
                        "temperature": 0.7,
                        "maxTokens": 1024
                    }
                }
                
                response = self.bedrock.converse(
                    modelId=self.model_id,
                    messages=request["messages"],
                    inferenceConfig=request["inferenceConfig"]
                )
                
                content_blocks = response["output"]["message"]["content"]
                question = ""
                for block in content_blocks:
                    if "text" in block:
                        question = block["text"].strip()
                        break
                
                # Replace the temporary user prompt in history with the assistant's response
                self.history.pop()  # Remove the temporary prompt
                self.history.append({
                    "role": "assistant",
                    "content": [{"text": question}]
                })
                
                logger.debug(f"Generated follow-up question: {question}")
                return question
                
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            # Return a fallback question
            return "Could you tell me more about your requirements for this project?"
    
    def generate_images(self, prompt: str) -> List[str]:
        """Generate images based on the gathered requirements."""
        try:
            # Configure tool for image generation
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
                                            "description": "Mandatory filename for the output image"
                                        }
                                    },
                                    "required": ["prompt"]
                                }
                            }
                        }
                    }
                ]
            }
            
            # Create a detailed prompt for image generation
            enhance_prompt = f"""Based on the following requirements for a {self.service_title} project, create a detailed image generation prompt:
            {prompt}
            
            Focus on:
            1. Visual style and aesthetics
            2. Key elements and composition
            3. Color scheme and mood
            4. Technical specifications
            
            Provide a detailed image generation prompt that will create an image matching these requirements using the generate_image tool."""
            
            # Add this prompt to the conversation
            request = {
                "messages": self.history + [{
                    "role": "user",
                    "content": [{"text": enhance_prompt}]
                }],
                "inferenceConfig": {
                    "temperature": 0.7,
                    "maxTokens": 2048
                }
            }
            
            # Send the request with tool configuration
            self.generated_images, result = self.handle_function_calling(request, tool_config)
            
            if "tool_result" in result and result["tool_result"].get("success"):
                image_path = result["tool_result"]["image_path"]
                logger.debug(f"Generated image: {image_path}")
                return [image_path]
            else:
                logger.error(f"Image generation failed: {result}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}", exc_info=True)
            return []
    
    def get_feedback(self, image_path: str, feedback: str) -> str:
        """Process user feedback on generated images and suggest improvements."""
        try:
            # Encode image to base64
            image_base64 = self.encode_image_to_base64(image_path)
            
            if not image_base64:
                logger.error("Failed to encode image")
                return "I couldn't process the image. Please try again."
            
            # Prepare the message for Claude with the image
            prompt = f"""The user provided the following feedback on the generated image for the {self.service_title} project:
            {feedback}
            
            Based on this feedback, what specific improvements should we make?
            Focus on actionable changes that can be implemented in the next version of the image."""
            
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
                                "text": prompt
                            }
                        ]
                    }
                ]
            }

            # Invoke Claude 
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )

            # Parse and return Claude's response
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
                
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            return "I'll make adjustments based on your feedback."
    
    def handle_function_calling(self, request, tool_config):
        """
        Handles function calling with Claude, including the image generation tool
        """
        try:
            # Step 1: Send initial request
            response = self.bedrock.converse(
                modelId=self.model_id,
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
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    filename = tool_input.get("filename", f"image-{timestamp}.png")

                    # Call the image generation function
                    generated_images, tool_result = self.generate_and_save_image(prompt, filename, self.generated_images)
                else:
                    tool_result = {"error": f"Unknown tool: {tool_name}"}

                # Step 3: Send the image and prompt directly to Claude
                if tool_result.get("success"):
                    claude_response = self.pass_to_claude(image_path=tool_result['image_path'])
                else:
                    claude_response = tool_result.get("error", "Unknown error")

                return generated_images, {
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

                return self.generated_images, {"final_response": text_response}

        except Exception as e:
            logger.error(f"Error in function calling: {str(e)}", exc_info=True)
            return self.generated_images, {"error": str(e)}
    
    def generate_and_save_image(self, prompt="A futuristic cityscape at sunset", filename=None, generated_images=None):
        """
        Generate an image using Stability SD3 model and save it to a file
        
        Args:
            prompt: Text prompt for image generation
            filename: Mandatory filename for the output image (default: timestamp-based name)
            
        Returns:
            Dictionary with image path and base64 string
        """
        try:
            # Ensure generated_images list exists
            if generated_images is None:
                generated_images = []
                
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
            response = self.bedrock.invoke_model(
                modelId="stability.stable-image-ultra-v1:1",
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
            logger.error(f"Error generating image: {str(e)}", exc_info=True)
            return generated_images, {"success": False, "Stability error": str(e)}
    
    def encode_image_to_base64(self, image_path):
        """Encode an image file to base64."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}", exc_info=True)
            return None
            
    def pass_to_claude(self, image_data=None, image_path=None):
        """Pass an image and text to Claude for analysis."""
        prompt_text = f"you are trying to help this user pick the perfect {self.service_title} image, \
                    ask questions about the specifications of the image to help another \
                    image generation model gauge exactly what the user wants. \
                    Never ask the same question three times in a row."
        try:
            # Prepare the image data - either use provided binary data or load from path
            if image_data is None and image_path:
                image_base64 = self.encode_image_to_base64(image_path)
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

            # Invoke Claude
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )

            # Parse and return Claude's response
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        except Exception as e:
            logger.error(f"Error with Claude analysis: {str(e)}", exc_info=True)
            return None
    
    def cleanup_generated_images(self):
        """Clean up any generated images"""
        for image_path in self.generated_images:
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.debug(f"Removed image: {image_path}")
                except Exception as e:
                    logger.error(f"Error removing image {image_path}: {str(e)}")