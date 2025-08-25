from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models import Service, User
from src.services.ai_service import AIBriefingService
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global AI briefing instance
ai_briefing = None

try:
    ai_briefing = AIBriefingService()
    logger.info("AI briefing system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize AI briefing system: {str(e)}", exc_info=True)
    ai_briefing = None


@api_bp.route('/briefing/set-service-title', methods=['POST'])
@login_required
def set_service_title():
    if not ai_briefing:
        logger.error("AI briefing system is not available")
        return jsonify({"error": "AI briefing system is not available"}), 503
        
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({"error": "Title is required"}), 400
            
        title = data['title']
        if not title.strip():
            return jsonify({"error": "Title cannot be empty"}), 400
            
        ai_briefing.set_service_title(title)
        logger.info(f"Successfully set service title to: {title}")
        
        test_question = ai_briefing.get_next_question()
        if not test_question:
            return jsonify({"error": "Unable to initialize the AI briefing with this title"}), 500
        
        return jsonify({
            "success": True, 
            "first_question": test_question
        })
        
    except Exception as e:
        logger.error(f"Error in set-service-title endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bp.route('/briefing/next-question', methods=['POST'])
@login_required
def get_next_question():
    if not ai_briefing:
        return jsonify({"error": "AI briefing system is not available"}), 503
        
    try:
        data = request.get_json() or {}
        user_input = data.get('message')
        
        if not ai_briefing.service_title:
            return jsonify({"error": "Service title must be set before starting the briefing"}), 400
        
        question = ai_briefing.get_next_question(user_input)
        
        image_urls = []
        if user_input:
            requirements = ""
            for msg in ai_briefing.history:
                if msg.get("role") == "user":
                    for content in msg.get("content", []):
                        if "text" in content:
                            requirements += content["text"] + " "
            
            generated_urls = ai_briefing.generate_images(requirements)
            if generated_urls:
                for url in generated_urls:
                    if url.startswith("generated_images/"):
                        image_urls.append("/" + url)
                    else:
                        image_urls.append(url)
        
        return jsonify({
            "success": True,
            "message": question or "Could you tell me more about your project requirements?",
            "images": image_urls
        })
        
    except Exception as e:
        logger.error(f"Error in next-question endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@api_bp.route('/briefing/generate-images', methods=['POST'])
@login_required
def generate_images():
    if not ai_briefing:
        return jsonify({"error": "AI briefing system is not available"}), 503
        
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        requirements = request.json.get('requirements')
        if not requirements:
            return jsonify({"error": "Requirements are needed to generate images"}), 400
            
        image_urls = ai_briefing.generate_images(requirements)
        
        web_urls = []
        for url in image_urls:
            if url.startswith("generated_images/"):
                web_urls.append("/" + url)
            else:
                web_urls.append(url)
                
        return jsonify({'image_urls': web_urls})
        
    except Exception as e:
        logger.error(f"Error generating images: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error generating images: {str(e)}"}), 500


@api_bp.route('/briefing/feedback', methods=['POST'])
@login_required
def process_feedback():
    if not ai_briefing:
        return jsonify({"error": "AI briefing system is not available"}), 503
        
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        image_url = request.json.get('image_url')
        feedback = request.json.get('feedback')
        
        if not image_url or not feedback:
            return jsonify({"error": "Both image_url and feedback are required"}), 400
        
        if image_url.startswith('/generated_images/'):
            image_url = image_url[1:]
            
        response = ai_briefing.get_feedback(image_url, feedback)
        
        requirements = ai_briefing.history[-1].get("content", [{}])[0].get("text", "") + " " + feedback
        new_image_urls = ai_briefing.generate_images(requirements)
        new_image_url = None
        if new_image_urls and len(new_image_urls) > 0:
            new_image_url = new_image_urls[0]
            if new_image_url.startswith("generated_images/"):
                new_image_url = "/" + new_image_url
                
        return jsonify({
            'response': response,
            'new_image_url': new_image_url
        })
        
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing feedback: {str(e)}"}), 500


@api_bp.route('/briefing/summarize', methods=['GET'])
@login_required
def summarize_briefing():
    if not ai_briefing:
        return jsonify({"error": "AI briefing system is not available"}), 503
    
    try:
        conversation_text = ""
        for msg in ai_briefing.history:
            role = msg.get("role", "")
            for content in msg.get("content", []):
                if "text" in content:
                    conversation_text += f"{role.upper()}: {content['text']}\n\n"
        
        summary_prompt = f"Based on our conversation about the {ai_briefing.service_title} project, please provide:\n\n1. A summary of key requirements\n2. The main goals of the project\n3. Style preferences and visual elements\n\nKeep your response concise and well-structured."
        
        summary_request = {
            "messages": ai_briefing.history + [{
                "role": "user",
                "content": [{"text": summary_prompt}]
            }],
            "inferenceConfig": {
                "temperature": 0.3,
                "maxTokens": 1024
            }
        }
        
        response = ai_briefing.bedrock.converse(
            modelId=ai_briefing.model_id,
            messages=summary_request["messages"],
            inferenceConfig=summary_request["inferenceConfig"]
        )
        
        content_blocks = response["output"]["message"]["content"]
        summary = ""
        for block in content_blocks:
            if "text" in block:
                summary = block["text"].strip()
                break
        
        final_image_urls = ai_briefing.generate_images(f"A finalized concept image for {ai_briefing.service_title} based on: {summary}")
        final_image_url = None
        if final_image_urls and len(final_image_urls) > 0:
            final_image_url = final_image_urls[0]
            if final_image_url.startswith("generated_images/"):
                final_image_url = "/" + final_image_url
        
        return jsonify({
            "summary": summary,
            "final_image_url": final_image_url
        })
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error generating summary: {str(e)}"}), 500


@api_bp.route('/contact-seller/<int:service_id>', methods=['POST'])
@login_required
def contact_seller(service_id):
    try:
        service = Service.query.get_or_404(service_id)
        seller = User.query.get_or_404(service.seller_id)
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        message = data.get('message')
        if not message:
            return jsonify({"error": "Message is required"}), 400
            
        return jsonify({
            "success": True,
            "message": "Message sent successfully",
            "seller": {
                "username": seller.username,
                "email": seller.email
            }
        })
        
    except Exception as e:
        logger.error(f"Error in contact-seller endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500