import google.generativeai as genai
from typing import List, Dict, Any
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIBriefingSystem:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key is required")
        genai.configure(api_key='AIzaSyAMgX9jDnSvVwcx23h77VfdyfaZS8tb-t0')
        
        # Create models with proper configuration
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize a chat session for maintaining proper conversation format
        self.chat = self.model.start_chat(history=[])
        self.service_title = None
        
    def set_service_title(self, title: str):
        """Set the service title for context"""
        if not title:
            raise ValueError("Service title is required")
        self.service_title = title
        logger.debug(f"Service title set to: {title}")
        
        # Reset chat when a new service title is set
        self.chat = self.model.start_chat(history=[])
        
    def get_next_question(self, user_input: str = None) -> str:
        """Get the next question to ask the user based on the conversation history."""
        if not self.service_title:
            raise ValueError("Service title must be set before getting questions")
        
        try:
            # If this is the first question and no user input yet
            if not user_input and len(self.chat.history) == 0:
                prompt = f"""You are an AI assistant helping to gather requirements for a {self.service_title} project.
                Start with the broadest possible question to understand what kind of project the client is looking for.
                Focus on understanding their overall vision and goals.
                Keep your response concise and focused on a single question.
                Do not mention specific details or technical requirements yet."""
                
                logger.debug(f"Generating first question with prompt: {prompt}")
                response = self.chat.send_message(prompt)
                
                if hasattr(response, 'text'):
                    question = response.text.strip()
                    logger.debug(f"Generated first question: {question}")
                    return question
                else:
                    logger.error(f"Unexpected response format: {response}")
                    return "Could you tell me about your project requirements?"
            
            # For subsequent interactions, add user input and get next question
            if user_input:
                logger.debug(f"Processing user input: {user_input}")
                
                # Add user input directly to the chat
                response = self.chat.send_message(user_input)
                
                # Now generate the next question based on conversation so far
                prompt = f"""You are continuing a conversation about a {self.service_title} project.
                Previous context from the conversation:
                {self.chat.history}
                
                Based on this context, ask the next most relevant question to gather more requirements.
                Your question should:
                1. Reference specific details the user has already shared
                2. Build upon previous answers to dig deeper
                3. Focus on understanding:
                   - The overall purpose and goals
                   - Target audience
                   - Style preferences
                   - Specific requirements
                   - Any constraints or limitations
                
                Keep your response concise and focused on a single question.
                Make sure your question feels natural and connected to the previous conversation."""
                
                response = self.chat.send_message(prompt)
                
                if hasattr(response, 'text'):
                    question = response.text.strip()
                    logger.debug(f"Generated follow-up question: {question}")
                    return question
                else:
                    logger.error(f"Unexpected response format: {response}")
                    return "What other requirements should I know about your project?"
                
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}", exc_info=True)
            # Return a fallback question
            return "Could you tell me more about your requirements for this project?"
    
    def generate_images(self, prompt: str) -> List[str]:
        """Generate images based on the gathered requirements."""
        try:
            # Create a detailed prompt for image generation
            image_prompt = f"""Based on the following requirements, generate a detailed description for an image:
            {prompt}
            
            Focus on:
            1. Visual style and aesthetics
            2. Key elements and composition
            3. Color scheme and mood
            4. Technical specifications
            
            Provide a detailed description that can be used to generate an image."""
            
            response = self.model.generate_content(image_prompt)
            
            if hasattr(response, 'text'):
                image_description = response.text.strip()
                logger.debug(f"Generated image description: {image_description[:100]}...")
                
                # Here you would integrate with an image generation API
                # For now, we'll return placeholder URLs
                # TODO: Replace with actual image generation
                return ["placeholder_image_url_1", "placeholder_image_url_2"]
            else:
                logger.error(f"Unexpected response format: {response}")
                return ["error_placeholder_image"]
                
        except Exception as e:
            logger.error(f"Error generating images: {str(e)}", exc_info=True)
            return ["error_placeholder_image"]
    
    def get_feedback(self, image_url: str, feedback: str) -> str:
        """Process user feedback on generated images and suggest improvements."""
        try:
            prompt = f"""The user provided the following feedback on the generated image:
            {feedback}
            
            Based on this feedback and our previous conversation about the {self.service_title} project, 
            what specific improvements should we make?
            Focus on actionable changes that can be implemented."""
            
            response = self.model.generate_content(prompt)
            
            if hasattr(response, 'text'):
                return response.text.strip()
            else:
                logger.error(f"Unexpected response format: {response}")
                return "I'll make adjustments based on your feedback."
                
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            return "I'll make adjustments based on your feedback."