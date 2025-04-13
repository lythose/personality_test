import numpy as np
import plotly.graph_objects as go
from PIL import Image

img_width=800
img_height=600

# Lambda functions 
axes_to_polar = lambda points: np.array([np.linalg.norm(points[1]-points[0]), np.atan2(points[1][1] - points[0][1], points[1][0] - points[0][0])])
get_position = lambda r, polar, points: points[0] + polar[0] * r**2.5 * np.array([np.cos(polar[1]),np.sin(polar[1])])

source = Image.open("./personality_test_app/images/personality.jpg")

def get_base_image() -> go.Figure:
    """ Get the base image figure for the results
    """
    fig = go.Figure()

    # Add the hexagon plot to the image
    fig.add_layout_image(
        x=0,
        sizex=img_width,
        y=0,
        sizey=img_height,
        xref="x",
        yref="y",
        opacity=1.0,
        layer="below",
        source=source
    )
    fig.update_xaxes(showgrid=False, range=(0, img_width))
    fig.update_yaxes(showgrid=False, scaleanchor='x', range=(img_height, 0))

    return fig

def get_result_plot(results: np.ndarray) -> go.Figure:
    """ Produce the test results

    results: [clown, hater, grinder, brick, sender, yapper]; values from 0.0 to 1.0
    """
    # Make sure none of the results are greater than 1.0 or less than 0.0
    results[np.where(results>1.0)[0]] = 1.0
    results[np.where(results<0.0)[0]] = 0.0

    # Axes of traits 
    # ----- [low[x,y],high[x,y]]
    clown = np.array([[407,230],[407,90]])
    hater = np.array([[466,262],[601,191]])
    grinder = np.array([[466,325],[601,395]])
    brick = np.array([[407,355],[407,494]])
    sender = np.array([[346,325],[214,395]])
    yapper = np.array([[346,261],[214,191]])

    # Polar coordinates 
    clown_r_th = axes_to_polar(clown)
    brick_r_th = axes_to_polar(brick)
    hater_r_th = axes_to_polar(hater)
    grinder_r_th = axes_to_polar(grinder)
    sender_r_th = axes_to_polar(sender)
    yapper_r_th = axes_to_polar(yapper)

    fig = get_base_image()

    # Get positions of all the results
    clown_out = get_position(results[0], clown_r_th, clown)
    hater_out = get_position(results[1], hater_r_th, hater)
    grinder_out = get_position(results[2], grinder_r_th, grinder)
    brick_out = get_position(results[3], brick_r_th, brick)
    sender_out = get_position(results[4], sender_r_th, sender)
    yapper_out = get_position(results[5], yapper_r_th, yapper)

    # plot the results on top of the image
    fig.add_scatter(name="Result",
                    x=[clown_out[0], hater_out[0], grinder_out[0], brick_out[0], sender_out[0], yapper_out[0]],
                    y=[clown_out[1], hater_out[1], grinder_out[1], brick_out[1], sender_out[1], yapper_out[1]],
                    fill="toself",
                    fillcolor="cyan",
                    opacity=0.7)
    
    return fig
