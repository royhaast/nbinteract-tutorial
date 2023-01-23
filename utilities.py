import numpy as np

import plotly
import plotly.graph_objs as go

import ipywidgets as widgets
from ipywidgets import interact, TwoByTwoLayout
from IPython.display import display

import matplotlib as mpl
import matplotlib.pyplot as plt

def load_data(filepath):
    return np.load(filepath, allow_pickle=True)['data'][..., None][0]

class visualize_surface_data(widgets.HBox):
    def __init__(self, data, figsize=(4,4)):
        plt.close(plt.gcf())
        
        self.data     = data
        self.subjects = list(data.keys())

        # Scene settings
        self.camera = dict(
            up=dict(x=0, y=0, z=1),
            eye=dict(x=1, y=2.5, z=1)
        )

        self.lighting_effects = dict(
            ambient=0.4, diffuse=0.5, roughness = 0.9, 
            specular=0.6, fresnel=0.2
        )        
        
        self.scene = dict(
            xaxis = dict(showbackground=False, visible=False),
            yaxis = dict(showbackground=False, visible=False),
            zaxis = dict(showbackground=False, visible=False)
        )

        self.margin = dict(l=0, r=0, b=0, t=0)

        self.settings = dict(
            width=400,
            height=400,
            scene=self.scene,
            scene_aspectmode='data',
            scene_camera=self.camera,
            margin=self.margin,
            showlegend=False,
            hovermode=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        widget=widgets.interactive(
            self.plot,
            subject=widgets.Dropdown(
                options=self.subjects, value=self.subjects[0], 
                disabled=False, description='Subject:'
            ),
            hemi=widgets.ToggleButtons(
                options=['Left','Right'],
                value='Left', description='Hemisphere:',
                button_style='', style={'button_width': 'auto'}
            ),            
            overlay=widgets.ToggleButtons(
                options=['Subfields','Thickness'],
                value='Subfields', description='Overlay:',
                button_style='', style={'button_width': 'auto'},
                layout=widgets.Layout(flex='1 3 auto', width='auto'),
            ),
            onoff = widgets.Checkbox(
                value=True, description='Show', indent=False,
                layout=widgets.Layout(flex='1 1 auto', width='auto'),
            )            
            
        )        
        
        overlay_controls = widgets.HBox(
            (widget.children[2], widget.children[3]),
            layout=widgets.Layout(display='flex', flex_flow='row', align_items='stretch')
        )
        
        controls_box = widgets.VBox(
            (widget.children[0], widget.children[1], overlay_controls),
            layout=widgets.Layout(display='flex', flex_flow='col wrap', align_items='stretch')
        )

        super().__init__(
            children=[controls_box, widget.children[-1]]
        )
        
    def plot(self, subject='Sub-01', hemi='Left', overlay='Subfields', onoff=True):
        self.subject = subject
        self.hemi    = hemi
        self.overlay = overlay if onoff else 'Plain'
        self.surf    = self.data[self.subject][self.hemi]
        self.cdata   = self.colormapper(
            self.overlay, self.surf[self.overlay]
        )
        
        self.surface_fig = go.FigureWidget(layout=self.settings)
        self.surface_fig.add_trace(
            go.Mesh3d(
                x=self.surf['Vertices'][:,0], 
                y=self.surf['Vertices'][:,1],
                z=self.surf['Vertices'][:,2],
                i=self.surf['Faces'][:,0],
                j=self.surf['Faces'][:,1],
                k=self.surf['Faces'][:,2],
                vertexcolor=self.cdata,
                lighting=self.lighting_effects
            )
        )   
        
        self.surface_fig.show()
        
    def colormapper(self, i, data):
        cdict = {
            'Plain': (mpl.cm.gray, 0, 2),
            'Subfields': (mpl.cm.tab10, 1, 10), 
            'Thickness': (mpl.cm.viridis, 0.5, 1.5)
        }

        norm   = mpl.colors.Normalize(vmin=cdict[i][1], vmax=cdict[i][2], clip=True)
        mapper = mpl.cm.ScalarMappable(norm=norm, cmap=cdict[i][0])

        return [ mapper.to_rgba(x) for x in data ]


class visualize_volume_data(widgets.HBox):
    def __init__(self, data, as_bg='T2w', cmap='gray', figsize=(4,4)):
        plt.close(plt.gcf())
        
        # Image data
        self.data     = data
        self.as_bg    = as_bg
        self.hemi     = 'Left'
        self.subjects = list(data.keys())
        self.overlays = list(data[self.subjects[0]][self.hemi].keys())
        
        # Initial plotting
        self.bg = np.transpose(
            self.data[self.subjects[0]][self.hemi][self.as_bg],
            [2,0,1]
        )
        
        self.max_slice     = self.bg.shape[2]-1
        self.current_slice = int(self.max_slice/2)
        
        plt.ioff()
        self.volume_fig, self.ax = plt.subplots(constrained_layout=True, figsize=figsize, facecolor=[0,0,0,0])
        plt.ion()
        self.volume_fig.canvas.toolbar_position = 'bottom'
        self.volume_fig.canvas.header_visible = False
        
        # Background image
        self.v = [
            np.percentile(self.bg, 5), np.percentile(self.bg, 95)
        ]
        self.img = plt.imshow(
            self.bg[:,:,self.current_slice],
            origin='lower', cmap=cmap, aspect='auto',
            vmin=self.v[0], vmax=self.v[1]
        )
        
        # Overlay
        self.overlay = np.transpose(
            self.data[self.subjects[0]][self.hemi]['Segmentation'],
            [2,0,1]
        )
        
        self.opacity = .5
        self.alpha=np.where(
            self.overlay[:,:,self.current_slice]>0,self.opacity,0
        ).astype(float)
        
        self.seg = plt.imshow(
            self.overlay[:,:,self.current_slice],
            origin='lower', cmap='tab10', aspect='auto',
            vmin=1, vmax=10, alpha=self.alpha
        )
        
        # Hide axes
        plt.xticks([]), plt.yticks([])

        widget=widgets.interactive(
            self.plot,
            subject=widgets.Dropdown(
                options=self.subjects, value=self.subjects[0], 
                disabled=False, description='Subject:'
            ),
            hemi=widgets.ToggleButtons(
                options=['Left','Right'],
                value='Left', description='Hemisphere:',
                button_style='', style={'button_width': 'auto'}
            ),
            crange = widgets.FloatRangeSlider(
                value=self.v,
                min=0, max=1500, step=1,
                description='T$_2$w range:',
                continuous_update=True,
                readout=True, readout_format='.0f',
            ),            
            z_slice=widgets.IntSlider(
                min=0, max=self.max_slice, step=1,
                value=self.current_slice, description='Slice:',
                continuous_update=True
            ),             
            overlay=widgets.ToggleButtons(
                options=['Segmentation','Subfields'],
                value='Segmentation', description='Overlay:',
                button_style='', style={'button_width': 'auto'},
                layout=widgets.Layout(flex='1 3 auto', width='auto'),
            ),
            onoff = widgets.Checkbox(
                value=True, description='Show', indent=False,
                layout=widgets.Layout(flex='1 1 auto', width='auto'),
            )
        )

        overlay_controls = widgets.HBox(
            (widget.children[3], widget.children[4]),
            layout=widgets.Layout(display='flex', flex_flow='row', align_items='stretch')
        )
        
        controls_box = widgets.VBox(
            (widget.children[0], widget.children[1], widget.children[2], overlay_controls, widget.children[5]),
            layout=widgets.Layout(display='flex', flex_flow='col wrap', align_items='stretch')
        )

        super().__init__(
            children=[controls_box, self.volume_fig.canvas]
        )

    def plot(self, subject='Sub-01', hemi='Left', crange=[0,100], overlay='Segmentation', onoff=True, z_slice=60):
        self.current_slice = z_slice
        self.hemi          = hemi
        
        # Update background image
        self.bg = np.transpose(
            self.data[subject][self.hemi][self.as_bg],
            [2,0,1]
        )
        
        self.v = [
            np.percentile(self.bg, 5), np.percentile(self.bg, 95)
        ]
        
        self.img.set_data(self.bg[:,:,self.current_slice])
        self.img.set_clim(vmin=crange[0], vmax=crange[1])
        
        # Update foreground image
        self.overlay = np.transpose(
            self.data[subject][self.hemi][overlay],
            [2,0,1]
        )      
        
        self.seg.set_data(self.overlay[:,:,self.current_slice])
        
        self.opacity = 0.5 if onoff else 0
        self.alpha=np.where(
            self.overlay[:,:,self.current_slice]>0, self.opacity, 0
        ).astype(float)
        self.seg.set_alpha(self.alpha)
        
        # Redraw
        self.volume_fig.canvas.draw()