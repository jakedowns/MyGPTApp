from datetime import datetime
from marshmallow import Schema, fields, pre_load
from mygptapp import ma
from mygptapp.models import Message

class OpenAIApiMessageSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Message
        fields = ('role', 'content')

class MessageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        include_fk = True

class MessageCreateSchema(Schema):
    class Meta:
        model = Message

    role = fields.Str(required=True)
    content = fields.Str(required=True)
    user_id = fields.Int(required=True)

    @pre_load
    def add_created_at(self, data, **kwargs):
        data['created_at'] = datetime.utcnow()
        return data