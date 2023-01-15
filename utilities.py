import plotly
import plotly.graph_objs as go
import ipywidgets as widgets
from ipywidgets import interact
import matplotlib as mpl

def colormapper(i, data):
    cdict = {
        0: (mpl.cm.gray, 0, 2),
        1: (mpl.cm.tab10, 1, 10), 
        2: (mpl.cm.viridis, 0.5, 1.5)
    }
    
    norm   = mpl.colors.Normalize(vmin=cdict[i][1], vmax=cdict[i][2], clip=True)
    mapper = mpl.cm.ScalarMappable(norm=norm, cmap=cdict[i][0])
    
    return [ mapper.to_rgba(x) for x in data ]

def plot_midthickness(data_dict):
    # Scene
    camera = dict(
        eye=dict(x=0, y=0, z=2.5)
    )

    scene = dict(
        xaxis = dict(showbackground=False, visible=False),
        yaxis = dict(showbackground=False, visible=False),
        zaxis = dict(showbackground=False, visible=False)
    )

    margin = dict(l=0, r=0, b=0, t=0)

    settings = dict(
        width=500,
        height=500,
        scene=scene,
        scene_aspectmode='data',
        scene_camera=camera,
        margin=margin,
        showlegend=False,
        hovermode=False
    )
       
    # Plot
    subjects = list(data_dict.keys())
    fig = go.FigureWidget()
    mesh = fig.add_trace(
        go.Mesh3d(
            x=data_dict[subjects[0]]['R'][0][:,0], 
            y=data_dict[subjects[0]]['R'][0][:,1],
            z=data_dict[subjects[0]]['R'][0][:,2],
            i=data_dict[subjects[0]]['R'][1][:,0],
            j=data_dict[subjects[0]]['R'][1][:,1],
            k=data_dict[subjects[0]]['R'][1][:,2],
        )
    )

    fig.update_layout(dict1=settings)
    
    @interact(
        Subject=subjects,
        Overlay=[('Plain', 0), ('Subfields', 1)] #, ('Thickness', 2)]
    )
    def update(Subject=[subjects[0]], Overlay=[('Plain', 0)]):
        with fig.batch_update():
            mesh.data[0].x = data_dict[Subject]['R'][0][:,0]
            mesh.data[0].y = data_dict[Subject]['R'][0][:,1]
            mesh.data[0].z = data_dict[Subject]['R'][0][:,2]

            mesh.data[0].i = data_dict[Subject]['R'][1][:,0]
            mesh.data[0].j = data_dict[Subject]['R'][1][:,1]
            mesh.data[0].k = data_dict[Subject]['R'][1][:,2]

            mesh.data[0].vertexcolor=colormapper(
                Overlay, data_dict[Subject]['R'][2][Overlay]
            )
            
    return fig