import numpy as np
from copy import deepcopy
import plotly.graph_objects as go
from dash import Dash, html, Input, Output, State, callback, ctx, dcc, clientside_callback
import dash_bootstrap_components as dbc
import json
import os

from personality_test import get_result_plot, get_base_image, get_meta_results, construct_meta_list

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
    "wanderer": 0.0, 
    "organizer": 0.0
}
original_results = deepcopy(test_results)

img_folder = "./personality_test_app/images/"
results_meme_srcs = {
    "clown": {"src": "meme_page_clown.png", 
              "title": "Welcome to the Clown Council"},
    "hater": {"src": "meme_page_hater.png", 
              "title": "You should go to therapy"},
    "grinder": {"src": "meme_page_grinder.png", 
                "title": "The shareholders are very pleased"},
    "brick": {"src": "meme_page_brick.png", 
              "title": "Please touch some grass"},
    "sender": {"src": "meme_page_sender.png", 
               "title": "Break a leg!"},
    "yapper": {"src": "meme_page_yapper.png", 
               "title": "Oh, PLEASE go on..."},
    "wanderer": {"src": "meme_page_wanderer.png",
                    "title": "Are you lost?"}, 
    "organizer": {"src": "meme_page_organizer.png", 
                  "title": "Born to Excel"},
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
form_conversion = np.array([3.25, 3.0, 2.0, 1.0, 0.0, -0.25])

entered_name = ""
troll_div = html.Div(
    id='troll_div',
    children=[
        html.P("Q0: What is your name?",id='troll_question'),
        dcc.Input(value=entered_name, id="troll_name")
    ],
    hidden=True,
)

form_div = html.Div(
    id='form_div',
    children=[
        html.P("Question",id='form_question'),
        html.P(id='question_debug',hidden=HIDE_DEBUG),
        html.P(id='score_debug',hidden=HIDE_DEBUG),
        dcc.RadioItems(options=form_options,id='form_select',className='radioItems')
    ],
    hidden=True
)

meta_div = html.Div(
    id='meta_div',
    children=[
        html.H2("Congrats! You're a ..."),
        html.H3("",id="meta_result_header"),
        html.Br(),
        html.Img(id='meme_img',
                 style={
                     "width": "25vw",
                     "height": "50%",
                 }
        ),
    ],
    hidden=True,
)

app = Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    [
        html.Div(
            dbc.Row(
                [
                    dbc.Col(
                        html.H1('Brainrot Personality Test'),
                    ),
                    dbc.Col(
                        html.Img(src=app.get_asset_url("subway_surfers.gif"),
                                 title="You're cooked",
                                 height="60px",
                                 width="100px")
                    ),
                ]
            ),
            style={
                "border": "2px #212121",
            }
        ),
        html.Br(),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                form_div,
                                troll_div,
                                html.P("Screenshot to share with your friends and/or coworkers! :)", id='screenshot_msg',hidden=True),
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
                                    hidden=HIDE_DEBUG, # Just to be able to skip to the end
                                ),
                                html.Button(
                                    "Start Over",
                                    id='reset_btn',
                                    disabled=True
                                ),
                                html.Br(),
                            ],
                            width=6,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    dcc.Graph(
                                        id='result_plot',
                                        figure=original_fig,
                                    ),
                                    id='results_graph_div',
                                    hidden=True,
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
                )
            ],
            style={
                "border": "5px #212121",
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
        ),
        dcc.Store(
            id='troll_entered_name',
            data=entered_name,
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
    Output('screenshot_msg','hidden',allow_duplicate=True),
    Output('troll_div','hidden',allow_duplicate=True),
    Output('troll_entered_name','data'),
    Input('next_btn','n_clicks'),
    Input('start_btn','n_clicks'),
    Input('reset_btn','n_clicks'),
    State('form_select','value'),
    State('q_index_stored','data'),
    State('test_results_stored','data'),
    State('question_ids_stored','data'),
    State('troll_name','value'),
    State('troll_entered_name','data'),
    prevent_initial_call=True
)
def cycle_questions(n1,n2,n3,selection,q_index,test_results:dict,question_ids,input_name,stored_name):
    local_test_results = deepcopy(test_results)
    hide_next_btn = False
    hide_result_btn = True
    hide_form_div = False
    disable_next_btn = True
    disable_reset_btn = True
    disable_start_btn = False
    hide_screenshot_msg = True
    hide_troll_question = True
    name_output = stored_name
    form_reset = None # reset the form value each time the questions are cycled
    if ctx.triggered_id in ['start_btn', 'reset_btn']:
        np.random.shuffle(question_ids) # randomize question order each time
        text = ""
        debug_text = ""
        score_debug_text = ""
        hide_troll_question = False
        hide_form_div = True
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
                score_debug_text,
                hide_screenshot_msg,
                hide_troll_question,
                name_output) 
    
    # Need to update the stored name after the first cycle
    if q_index == 0 and len(stored_name) == 0:
        name_output = input_name
        # Do a little trolling
        if input_name.lower() in ["nic", "nicolas"]:
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
                    score_debug_text,
                    hide_screenshot_msg,
                    hide_troll_question,
                    name_output)
        
        else:
            # Need to set up for the next question with the current q index
            text = f"Q{q_index+1}/{len(questions_json)}: {questions_json[question_ids[q_index]]['text']}"
            debug_text = f"[{questions_json[question_ids[q_index]]['type']}]"
            score_debug_text = f"{[f'{itype, float(score)}' for itype, score in local_test_results.items()]}"

            return (text, 
                    hide_next_btn, 
                    hide_result_btn, 
                    hide_form_div, 
                    disable_next_btn, 
                    disable_reset_btn, 
                    disable_start_btn, 
                    form_reset, 
                    local_test_results, 
                    q_index,
                    question_ids, 
                    debug_text, 
                    score_debug_text, 
                    hide_screenshot_msg,
                    hide_troll_question,
                    name_output)
    
    else:
        # Get necessary info for incrementing results of the question that was just answered
        scale = questions_json[question_ids[q_index]]['scale']
        architype = questions_json[question_ids[q_index]]['type']

        # Increment results
        if type(architype) == list:
            for idx, item in enumerate(architype):
                local_test_results[item] = local_test_results[item] + form_conversion[np.where(selection==np.array(form_options))][0] * scale[idx] / 18.0
        else:
            local_test_results[architype] = local_test_results[architype] + form_conversion[np.where(selection==np.array(form_options))][0] * scale / 18.0
    
        # Return if the last question was just answered
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
                    score_debug_text,
                    hide_screenshot_msg,
                    hide_troll_question,
                    name_output)

        else:
            # Need to set up for the next question
            q_index += 1
            text = f"Q{q_index+1}/{len(questions_json)}: {questions_json[question_ids[q_index]]['text']}" # we're zero indexing now :(
            debug_text = f"[{questions_json[question_ids[q_index]]['type']}]"
            score_debug_text = f"{[f'{itype, float(score)}' for itype, score in local_test_results.items()]}"

            return (text, 
                    hide_next_btn, 
                    hide_result_btn, 
                    hide_form_div, 
                    disable_next_btn, 
                    disable_reset_btn, 
                    disable_start_btn, 
                    form_reset, 
                    local_test_results, 
                    q_index,
                    question_ids, 
                    debug_text, 
                    score_debug_text, 
                    hide_screenshot_msg,
                    hide_troll_question,
                    name_output)


@callback(
    Output('result_plot','figure',allow_duplicate=True),
    Output('results_graph_div','hidden',allow_duplicate=True),
    Output('next_btn','hidden',allow_duplicate=True),
    Output('test_results_stored','data',allow_duplicate=True),
    Output('q_index_stored','data',allow_duplicate=True),
    Output('meta_result_header','children',allow_duplicate=True),
    Output('meta_div','hidden',allow_duplicate=True),
    Output('meme_img','src',allow_duplicate=True),
    Output('meme_img','title',allow_duplicate=True),
    Output('screenshot_msg','hidden',allow_duplicate=True),
    Output('troll_div','hidden',allow_duplicate=True),
    Input('result_btn','n_clicks'),
    State('test_results_stored','data'),
    State('troll_entered_name','data'),
    prevent_initial_call=True
)
def return_test_results(n,test_results: dict, stored_name: str):
    results = np.array(list(test_results.values()))
    idx_max = np.where(results == np.max(results))[0][0]
    type_max = list(test_results.keys())[idx_max]
    # We do a little trolling
    if stored_name.lower() in ["nic", "nicolas"]:
        img_src = "software_results.png"
        img_alt = "Hate to break the news to you like this, bud"
        meta_children = [html.Ul(id='meta_list', children=[html.Li("Software Engineer")])]
    else:
        img_src = results_meme_srcs[type_max]["src"]
        img_alt = results_meme_srcs[type_max]["title"]
        meta_results_text = get_meta_results(results, meta_json)
        meta_children = construct_meta_list(meta_results_text)
    q_index = 0
    hide_plot = False
    return get_result_plot(results), hide_plot, True, deepcopy(original_results), q_index, meta_children, False, app.get_asset_url(img_src), img_alt, False, True

@callback(
    Output('result_plot','figure',allow_duplicate=True),
    Output('results_graph_div','hidden',allow_duplicate=True),
    Output('test_results_stored','data',allow_duplicate=True),
    Output('q_index_stored','data',allow_duplicate=True),
    Output('meta_div','hidden',allow_duplicate=True),
    Output('screenshot_msg','hidden',allow_duplicate=True),
    Output('troll_div','hidden',allow_duplicate=True),
    Output('troll_entered_name','data',allow_duplicate=True),
    Output('troll_name','value',allow_duplicate=True),
    Input('reset_btn','n_clicks'),
    prevent_initial_call=True
)
def reset_results(n):
    fig = get_base_image()
    q_index = 0
    hide_plot = True
    reset_name = ""
    return fig, hide_plot, deepcopy(original_results), q_index, True, True, True, reset_name, reset_name

@callback(
    Output('next_btn','disabled',allow_duplicate=True),
    Input('form_select','value'),
    Input('troll_name','value'),
    State('troll_div','hidden'),

    prevent_initial_call=True,
)
def enable_next_btn(v, name_input,troll_div_hidden):
    """ Just enables the next button whenever something is selected
    """
    if v is not None or (len(name_input) > 0 and not troll_div_hidden):
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