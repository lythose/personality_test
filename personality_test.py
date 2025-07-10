import numpy as np
import plotly.graph_objects as go
from PIL import Image
import json
from dash import html

# Lambda functions 
axes_to_polar = lambda points: np.array([np.linalg.norm(points[1]-points[0]), np.atan2(points[1][1] - points[0][1], points[1][0] - points[0][0])])
get_position = lambda r, polar, points: points[0] + polar[0] * r**2.5 * np.array([np.cos(polar[1]),np.sin(polar[1])])

# source = Image.open("./images/personality.jpg") # use this when running from the .bat file
source = Image.open("./personality_test_app/images/personality.jpg")

def get_base_image() -> go.Figure:
    """ Get the base image figure for the results
    """
    fig = go.Figure()
    sizex, sizey = source.size

    # Add the hexagon plot to the image
    fig.add_layout_image(
        x=0,
        sizex=sizex,
        y=0,
        sizey=sizey,
        xref="x",
        yref="y",
        opacity=1.0,
        layer="below",
        source=source
    )
    fig.update_xaxes(dict(showgrid=False, range=(0, sizex), visible=False))
    fig.update_yaxes(dict(showgrid=False, scaleanchor='x', range=(sizey, 0), visible=False))
    fig.update_layout(width=sizex, height=sizey, plot_bgcolor='#ffffff')

    return fig

def get_result_plot(results: np.ndarray) -> go.Figure:
    """ Produce the test results

    results: [clown, hater, grinder, brick, sender, yapper, wanderer, organizer]; values from 0.0 to 1.0
    """
    # Make sure none of the results are greater than 1.0 or less than 0.0
    results[np.where(results>1.0)[0]] = 1.0
    results[np.where(results<0.0)[0]] = 0.0

    # Axes of traits 
    # -------------------- [low[x,y],high[x,y]]
    clown      = np.array([[253,210],[115,152]])
    wanderer = np.array([[290,171],[233,34]])
    hater      = np.array([[345,171],[402,34]])
    grinder    = np.array([[383,210],[520,152]])
    brick      = np.array([[383,264],[520,321]])
    organizer  = np.array([[345,302],[402,439]])
    yapper     = np.array([[290,302],[233,439]])
    sender     = np.array([[253,264],[115,321]])

    fig = get_base_image()

    # Get positions of all the results
    clown_out = get_position(results[0], axes_to_polar(clown), clown)
    hater_out = get_position(results[1], axes_to_polar(hater), hater)
    grinder_out = get_position(results[2], axes_to_polar(grinder), grinder)
    brick_out = get_position(results[3], axes_to_polar(brick), brick)
    sender_out = get_position(results[4], axes_to_polar(sender), sender)
    yapper_out = get_position(results[5], axes_to_polar(yapper), yapper)
    wanderer_out = get_position(results[6], axes_to_polar(wanderer), wanderer)
    organizer_out = get_position(results[7], axes_to_polar(organizer), organizer)

    # plot the results on top of the image
    fig.add_scatter(name="Result",
                    x=[clown_out[0], wanderer_out[0], hater_out[0], grinder_out[0], brick_out[0], organizer_out[0], yapper_out[0], sender_out[0]],
                    y=[clown_out[1], wanderer_out[1], hater_out[1], grinder_out[1], brick_out[1], organizer_out[1], yapper_out[1], sender_out[1]],
                    fill="toself",
                    fillcolor="cyan",
                    opacity=0.7)
    
    return fig

def get_meta_results(results: np.ndarray, meta_dict: dict):
    """ Process results to see if there is a metatype 

    returns: string for the name of the meta type
    """

    meta_array = np.array([list(meta.values())[0:-1] for meta in list(meta_dict.values())]).T

    # using the square to eliminate all the irrelevant scores from each meta type and then comparing against the original array 
    comparison = np.all(np.equal((results.reshape(8,1) * meta_array - meta_array**2) > 0, meta_array > 0),axis=0)

    # get the index of the meta type
    meta_results = []
    if len(np.where(comparison)[0]) > 0:
        meta_result_idx = np.where(comparison)[0]

        # get the top 3 meta traits
        for i, idx in enumerate(meta_result_idx):
            meta_results.append(list(meta_dict.values())[idx]['type'])
            if i == 2:
                break

        return meta_results
    
    else:
        return ["Yourself!"] # we can't figure out what you are :)

def construct_meta_list(results: list):
    """Just constructs the meta list object for display"""
    children = [html.Ul(id='meta_list', children=[html.Li(m) for m in results])]
    return children

if __name__=="__main__":
    with open('./personality_test_app/meta_traits.json', encoding="utf8") as f:
        meta_json = json.load(f)

    # none testing
    # results = np.linspace(0,.1,8)

    # one testing
    # results = np.linspace(0,1,8)

    # n testing
    results = np.ones(8) 

    get_meta_results(results,meta_json)