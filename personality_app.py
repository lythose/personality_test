import numpy as np
from copy import deepcopy
import plotly.graph_objects as go
from dash import Dash, html, Input, Output, State, callback, ctx, dcc
import dash_bootstrap_components as dbc
import json

from personality_test import get_result_plot, get_base_image

original_fig = get_base_image()

# Dictionary to update as the test is taken
test_results = {
    "clown": 0.0,
    "hater": 0.0,
    "grinder": 0.0,
    "brick": 0.0,
    "sender": 0.0,
    "yapper": 0.0,
}
original_results = deepcopy(test_results)

questions_json: dict = {}
with open('./personality_test_app/questions.json', encoding="utf8") as f:
    questions_json = json.load(f)
question_ids = np.array(list(questions_json.keys()))

q_index = 0
scale = 0
architype = None
form_options = ["Strongly Agree", "Agree", "Slightly Agree", "Slightly Disagree", "Disagree", "Strongly Disagree"]
form_conversion = np.array([5.0, 4.0, 3.0, 2.0, 1.0, 0.0])

form_div = html.Div(
    id='form_div',
    children=[
        html.P("Question",id='form_question'),
        dcc.RadioItems(options=form_options,id='form_select')
    ],
    hidden=True
)

app = Dash(__name__)
app.layout = html.Div(
    [
        html.H1('Brainrot Personality Test'),
        form_div,
        html.Br(),
        html.Button(
            "Start Questions",
            id='start_btn',
        ),
        html.Button(
            "Next Question",
            id='next_btn',
            hidden=True,
            disabled=True,
        ),
        html.Button(
            "Get Results!",
            id='result_btn',
            hidden=True,
        ),
        html.Button(
            "Start Over",
            id='reset_btn',
            disabled=True
        ),
        dcc.Graph(
            id='result_plot',
            figure=original_fig,
            style={'width': '90%', 'height': '90vh'},
        ),
    ]
)

app.title = 'Brainrot Personality Test'

@callback(
    Output('form_question','children'),
    Output('next_btn','hidden',allow_duplicate=True),
    Output('result_btn','hidden',allow_duplicate=True),
    Output('form_div','hidden',allow_duplicate=True),
    Output('next_btn','disabled',allow_duplicate=True),
    Output('reset_btn','disabled',allow_duplicate=True),
    Output('start_btn','disabled',allow_duplicate=True),
    Output('form_select','value'),
    Input('next_btn','n_clicks'),
    Input('start_btn','n_clicks'),
    Input('reset_btn','n_clicks'),
    State('form_select','value'),
    prevent_initial_call=True
)
def cycle_questions(n1,n2,n3,selection):
    global q_index 
    global scale
    global architype
    hide_next_btn = False
    hide_result_btn = True
    hide_form_div = False
    disable_next_btn = True
    disable_reset_btn = True
    disable_start_btn = False
    form_reset = None # reset the form value each time the questions are cycled
    if ctx.triggered_id in ['start_btn', 'reset_btn']:
        np.random.shuffle(question_ids) # randomize question order each time
        q_index = 0
        scale = questions_json[question_ids[q_index]]['scale']
        architype = questions_json[question_ids[q_index]]['type']
        text = f'Q{q_index + 1}/{len(questions_json)}: {questions_json[question_ids[q_index]]['text']}' # we 1 index here :)
        q_index += 1
        # Reset the internal test results 
        global test_results
        test_results = deepcopy(original_results)
        return text, hide_next_btn, hide_result_btn, hide_form_div, disable_next_btn, disable_reset_btn, disable_start_btn, form_reset

    if q_index == len(questions_json):

        text = "Get your results!!!!"
        hide_next_btn = True
        hide_form_div = True
        hide_result_btn = False
        disable_reset_btn = False
        disable_start_btn = True

        return text, hide_next_btn, hide_result_btn, hide_form_div, disable_next_btn, disable_reset_btn, disable_start_btn, form_reset
    
    # Get necessary info for incrementing results
    scale = questions_json[question_ids[q_index]]['scale']
    architype = questions_json[question_ids[q_index]]['type']
    text = f'Q{q_index + 1}/{len(questions_json)}: {questions_json[question_ids[q_index]]['text']}' # and here :)

    # Increment results
    test_results[architype] = test_results[architype] + form_conversion[np.where(selection==np.array(form_options))][0] * scale / np.max(form_conversion) / 6
    q_index += 1

    return text, hide_next_btn, hide_result_btn, hide_form_div, disable_next_btn, disable_reset_btn, disable_start_btn, form_reset


@callback(
    Output('result_plot','figure',allow_duplicate=True),
    Output('next_btn','hidden',allow_duplicate=True),
    Input('result_btn','n_clicks'),
    prevent_initial_call=True
)
def return_test_results(n):
    global test_results
    results = np.array(list(test_results.values()))
    test_results = deepcopy(original_results)
    return get_result_plot(results), True

@callback(
    Output('result_plot','figure',allow_duplicate=True),
    # Output('next_btn','hidden',allow_duplicate=True),
    Input('reset_btn','n_clicks'),
    prevent_initial_call=True
)
def reset_results(n):
    fig = get_base_image()
    return fig

@callback(
    Output('next_btn','disabled',allow_duplicate=True),
    Input('form_select','value'),
    prevent_initial_call=True,
)
def enable_next_btn(v):
    """ Just enables the next button whenever something is selected
    """
    if v is not None:
        return False
    return True

if __name__ == '__main__':
    app.run(debug=False)