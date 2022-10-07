from flask_wtf import *
from wtforms import *
from wtforms.validators import *

class StopButton(FlaskForm):
    stop=SubmitField('机器人返航')