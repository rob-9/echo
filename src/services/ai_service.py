import boto3
import json
import base64
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AIBriefingService:
    def __init__(self, region_name="us-west-2"):
        """Initialize the AI Briefing System with Bedrock client"""
        try:
            self.bedrock = boto3.client("bedrock-runtime", region_name=region_name)
            self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
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
        
        self.history = []
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
            if user_input and user_input.strip():
                self.history.append({
                    "role": "user",
                    "content": [{"text": user_input.strip()}]
                })
            
            prompt = f"Based on our conversation about the {self.service_title} project, ask a specific, targeted question to better understand the client's requirements. Keep it conversational and focused."
            
            self.history.append({
                "role": "user",
                "content": [{"text": prompt}]
            })
            
            response = self.bedrock.converse(
                modelId=self.model_id,
                messages=self.history,
                inferenceConfig={
                    "temperature": 0.7,
                    "maxTokens": 512
                }
            )
            
            content_blocks = response["output"]["message"]["content"]
            question = ""
            for block in content_blocks:
                if "text" in block:
                    question = block["text"].strip()
                    break
            
            if question:
                self.history.append({
                    "role": "assistant",
                    "content": [{"text": question}]
                })
            
            return question
            
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            return "Could you tell me more about your project requirements?"
    
    def generate_images(self, requirements: str) -> List[str]:
        """Generate images based on requirements"""
        try:
            os.makedirs("generated_images", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"concept-{timestamp}.png"
            output_path = os.path.join("generated_images", filename)
            
            payload = {
                "prompt": f"Professional design concept: {requirements}",
                "mode": "text-to-image",
                "output_format": "png",
                "seed": 0,
                "aspect_ratio": "1:1"
            }
            
            response = self.bedrock.invoke_model(
                modelId="stability.stable-image-ultra-v1:1",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            
            result = json.loads(response['body'].read())
            image_base64 = result['images'][0]
            
            image_bytes = base64.b64decode(image_base64)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
                
            self.generated_images.append(output_path)
            return [output_path]
            
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}", exc_info=True)
            return []
    
    def get_feedback(self, image_url: str, feedback: str) -> str:
        """Process feedback on an image"""
        try:
            feedback_prompt = f"The user provided this feedback on the generated image: {feedback}. Please acknowledge the feedback and ask a follow-up question to refine the design further."
            
            self.history.append({
                "role": "user",
                "content": [{"text": feedback_prompt}]
            })
            
            response = self.bedrock.converse(
                modelId=self.model_id,
                messages=self.history,
                inferenceConfig={
                    "temperature": 0.7,
                    "maxTokens": 512
                }
            )
            
            content_blocks = response["output"]["message"]["content"]
            response_text = ""
            for block in content_blocks:
                if "text" in block:
                    response_text = block["text"].strip()
                    break
            
            if response_text:
                self.history.append({
                    "role": "assistant",
                    "content": [{"text": response_text}]
                })
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            return "Thank you for the feedback. Could you tell me more about what you'd like to adjust?"