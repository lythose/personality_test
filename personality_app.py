import numpy as np
from copy import deepcopy
import plotly.graph_objects as go
from dash import Dash, html, Input, Output, State, callback, ctx, dcc, clientside_callback
import dash_bootstrap_components as dbc
import json
import os

from personality_test import get_result_plot, get_base_image, get_meta_results

external_stylesheets = [dbc.themes.BOOTSTRAP]

original_fig = get_base_image()
HIDE_DEBUG = True # Disable to see question mapping and scores while taking the test

# Dictionary to update as the test is taken
test_results = {
    "clown": 0.0,
    "hater": 0.0,
    "grinder": 0.0,
    "brick": 0.0,
    "sender": 0.0,
    "yapper": 0.0,
    "instigator": 0.0, 
    "organizer": 0.0
}
original_results = deepcopy(test_results)

img_folder = "./personality_test_app/images/"
results_meme_srcs = {
    "clown": {"src": "clown_meme.jpg", 
              "title": "Welcome to the Clown Council"},
    "hater": {"src": "hater_meme.jpg", 
              "title": "You should go to therapy"},
    "grinder": {"src": "grinder_meme.jpg", 
                "title": "The shareholders are very pleased"},
    "brick": {"src": "brick_meme.jpg", 
              "title": "Please touch some grass"},
    "sender": {"src": "sender_meme.jpg", 
               "title": "Break a leg!"},
    "yapper": {"src": "yapper_meme.jpg", 
               "title": "Oh, PLEASE go on..."},
    "instigator": {"src": "instigator_meme.jpg",
                    "title": "Are you a secret politician?"}, 
    "organizer": {"src": "organizer_meme.jpg", 
                  "title": ""},
}

questions_json: dict = {}
# with open('./questions.json', encoding="utf8") as f:  # use this when running from the .bat file
with open('./personality_test_app/questions.json', encoding="utf8") as f:
    questions_json = json.load(f)
question_ids = np.array(list(questions_json.keys()))

meta_json: dict = {}
with open('./personality_test_app/meta_traits.json', encoding="utf8") as f:
    meta_json = json.load(f)

q_index = 0
form_options = ["Strongly Agree", "Agree", "Slightly Agree", "Slightly Disagree", "Disagree", "Strongly Disagree"]
form_conversion = np.array([4.0, 3.0, 2.0, 1.0, 0.0, -1.0])

form_div = html.Div(
    id='form_div',
    children=[
        html.P("Question",id='form_question'),
        html.P(id='question_debug',hidden=HIDE_DEBUG),
        html.P(id='score_debug',hidden=HIDE_DEBUG),
        dcc.RadioItems(options=form_options,id='form_select')
    ],
    hidden=True
)

meta_div = html.Div(
    id='meta_div',
    children=[
        html.H2("Congrats! You're a ..."),
        html.H3("",id="meta_result_header"),
        html.P("lorem ipsum",id="meta_description"),
        html.Br(),
        html.Img(id='meme_img',
                 style={
                     "width": "50%",
                     "height": "50%",
                 }
        ),
    ],
    hidden=True,
)

app = Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    [
        html.H1('Brainrot Personality Test'),
        html.Br(),
        html.Div(
            dbc.Row(
                [
                    dbc.Col(
                        [
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
                            ),
                            html.Br(),
                        ],
                        width="auto",
                        
                    ), 
                    dbc.Col(
                        [
                            meta_div,
                        ],
                        width="auto",
                    )
                ]
            ),
            style={
                "border": "5px solid white",
            }
        ),
        # meta_div,
        dcc.Store( # Stores the test results client side 
            id='test_results_stored',
            data=original_results,
            storage_type='memory',
        ),
        dcc.Store( # Stores the question index that is currently active client side
            id='q_index_stored',
            data=q_index,
            storage_type='memory',
        ),
        dcc.Store( # Stores the list of question ids in their randomized order client side
            id='question_ids_stored',
            data=question_ids,
            storage_type='memory',
        )
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
    Output('test_results_stored','data',allow_duplicate=True),
    Output('q_index_stored','data',allow_duplicate=True),
    Output('question_ids_stored','data',allow_duplicate=True),
    Output('question_debug','children'),
    Output('score_debug','children'),
    Input('next_btn','n_clicks'),
    Input('start_btn','n_clicks'),
    Input('reset_btn','n_clicks'),
    State('form_select','value'),
    State('q_index_stored','data'),
    State('test_results_stored','data'),
    State('question_ids_stored','data'),
    prevent_initial_call=True
)
def cycle_questions(n1,n2,n3,selection,q_index,test_results:dict,question_ids):
    local_test_results = deepcopy(test_results)
    hide_next_btn = False
    hide_result_btn = True
    hide_form_div = False
    disable_next_btn = True
    disable_reset_btn = True
    disable_start_btn = False
    form_reset = None # reset the form value each time the questions are cycled
    if ctx.triggered_id in ['start_btn', 'reset_btn']:
        np.random.shuffle(question_ids) # randomize question order each time
        text = f'Q1/{len(questions_json)}: {questions_json[question_ids[0]]['text']}' # we 1 index here :)
        debug_text = f'[{questions_json[question_ids[0]]['type']}]'
        score_debug_text = ''
        return (text, 
                hide_next_btn,
                hide_result_btn, 
                hide_form_div,
                disable_next_btn, 
                disable_reset_btn, 
                disable_start_btn, 
                form_reset, 
                deepcopy(original_results), 
                0,
                question_ids,
                debug_text,
                score_debug_text) 

    if q_index+1 == len(questions_json):
        text = ''
        hide_next_btn = True
        hide_form_div = True
        hide_result_btn = False
        disable_reset_btn = False
        disable_start_btn = True
        debug_text = ''
        score_debug_text = ''

        return (text,
                hide_next_btn,
                hide_result_btn,
                hide_form_div,
                disable_next_btn,
                disable_reset_btn,
                disable_start_btn,
                form_reset,
                local_test_results, # <-- want these to stay the same until the results are returned
                q_index,            # <--
                question_ids, 
                debug_text,
                score_debug_text)
    
    # Get necessary info for incrementing results
    scale = questions_json[question_ids[q_index]]['scale']
    architype = questions_json[question_ids[q_index]]['type']

    # Increment results
    if type(architype) == list:
        for idx, item in enumerate(architype):
            local_test_results[item] = local_test_results[item] + form_conversion[np.where(selection==np.array(form_options))][0] * scale[idx] / 18.0
    else:
        local_test_results[architype] = local_test_results[architype] + form_conversion[np.where(selection==np.array(form_options))][0] * scale / 18.0
    
    q_index += 1
    text = f'Q{q_index+1}/{len(questions_json)}: {questions_json[question_ids[q_index]]['text']}' # and here :)
    debug_text = f'[{questions_json[question_ids[q_index]]['type']}]'
    score_debug_text = f'{[f'{itype, float(score)}' for itype, score in local_test_results.items()]}'

    return text, hide_next_btn, hide_result_btn, hide_form_div, disable_next_btn, disable_reset_btn, disable_start_btn, form_reset, local_test_results, q_index, question_ids, debug_text, score_debug_text


@callback(
    Output('result_plot','figure',allow_duplicate=True),
    Output('next_btn','hidden',allow_duplicate=True),
    Output('test_results_stored','data',allow_duplicate=True),
    Output('q_index_stored','data',allow_duplicate=True),
    Output('meta_result_header','children',allow_duplicate=True),
    Output('meta_div','hidden',allow_duplicate=True),
    Output('meme_img','src',allow_duplicate=True),
    Output('meme_img','title',allow_duplicate=True),
    Input('result_btn','n_clicks'),
    State('test_results_stored','data'),
    prevent_initial_call=True
)
def return_test_results(n,test_results: dict):
    results = np.array(list(test_results.values()))
    idx_max = np.where(results == np.max(results))[0][0]
    type_max = list(test_results.keys())[idx_max]
    img_src = results_meme_srcs[type_max]["src"]
    img_alt = results_meme_srcs[type_max]["title"]
    meta_results_text = get_meta_results(results, meta_json)
    q_index = 0
    return get_result_plot(results), True, deepcopy(original_results), q_index, meta_results_text, False, app.get_asset_url(img_src), img_alt

@callback(
    Output('result_plot','figure',allow_duplicate=True),
    Output('test_results_stored','data',allow_duplicate=True),
    Output('q_index_stored','data',allow_duplicate=True),
    Output('meta_div','hidden',allow_duplicate=True),
    Input('reset_btn','n_clicks'),
    prevent_initial_call=True
)
def reset_results(n):
    fig = get_base_image()
    q_index = 0
    return fig, deepcopy(original_results), q_index, True

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
    # -- For "production"
    # Run this at every start up in order to enable 8080 port forwarding
    # os.system('telnet google.com 443') 

    # Uncomment and change this to host computer IP when running  
    # app.run(host="0.0.0.0",port='8080')

    # -- For running locally for testing
    app.run(debug=False)