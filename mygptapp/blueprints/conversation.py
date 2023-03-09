# from flask import Blueprint, request, jsonify
# from flask_socketio import emit
# from mygptapp import db, socketio, app
# from mygptapp.models import Conversation, Message, User, OpenAIApiMessageSchema
# from jobs import process_prompt

# conversation_bp = Blueprint('conversation_bp', __name__)

# # POST route to submit a new prompt to a conversation
# @conversation_bp.route('/c/<int:convo_id>/prompt', methods=['POST'])
# @jwt_required
# def submit_prompt(convo_id):
#     user_id = get_jwt_identity()
#     prompt_text = request.json['prompt']
#     conversation = Conversation.query.get_or_404(convo_id)

#     if user_id not in [user.id for user in conversation.users]:
#         return jsonify({"error": "User is not authorized for this conversation"}), 403

#     prompt = Message(convo_id=convo_id, user_id=user_id, content=prompt_text, is_inner_thought=False)
#     db.session.add(prompt)

#     conversation.bot_holds_lock = True
#     db.session.commit()

#     # emit socket event
#     socketio.emit('prompt_received', {'status': 'thinking'}, room=conversation.id)

#     # process prompt in a background job
#     job = process_prompt.delay(prompt.id)

#     return jsonify({"success": "Prompt added successfully", "bot_holds_lock": True}), 200


# # GET route to interrupt the bot and force it to return the current prompt
# @conversation_bp.route('/c/<int:convo_id>/interrupt', methods=['GET'])
# @jwt_required
# def interrupt_bot(convo_id):
#     user_id = get_jwt_identity()
#     conversation = Conversation.query.get_or_404(convo_id)

#     if user_id not in [user.id for user in conversation.users]:
#         return jsonify({"error": "User is not authorized for this conversation"}), 403

#     # emit socket event
#     socketio.emit('bot_interrupted', {'status': 'interrupted'}, room=conversation.id)

#     # update conversation record, set bot_holds_lock to False
#     conversation.bot_holds_lock = False
#     db.session.commit()

#     return jsonify({"success": "Bot interrupted successfully"}), 200
