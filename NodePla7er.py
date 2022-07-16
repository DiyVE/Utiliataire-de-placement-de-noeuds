from logging import root
import math
import tkinter as tk
from matplotlib.pyplot import fill
from requests import delete
from tkcolorpicker import askcolor
from PIL import Image, ImageTk
from cv2 import resize
import filemanager as fm
import networkmanager as nm
import time
from pygame import mixer
from tkinter.filedialog import asksaveasfilename, askopenfilename


class Canvas_Node():
    def __init__(self, canvas, node_id, px_init_x_pos=None, px_init_y_pos=None, real_init_x_pos=None, real_init_y_pos=None, radius=10, color='red'):
        self.canvas = canvas
        self.node_id = node_id
        self.radius = radius
        self.color = color
        self.real_pos = [0, 0]
        self.px_pos = [0, 0]

        if px_init_x_pos is not None and px_init_y_pos is not None:
            self.px_pos = [px_init_x_pos, px_init_y_pos]
            self.real_pos = self.get_real_pos_from_px(self.px_pos)
        elif real_init_x_pos is not None and real_init_y_pos is not None:
            self.real_pos = [real_init_x_pos, real_init_y_pos]
            self.px_pos = self.get_px_pos_from_real(self.real_pos)
        else:
            raise ValueError('You must specify either the pixel position or the real position of the node')
        
        self.tk_node_id, self.tk_label_id = self.create_node()

    def create_node(self):
        tk_node_id = self.canvas.create_oval(self.px_pos[0] - self.radius, self.px_pos[1] - self.radius, self.px_pos[0] + self.radius, self.px_pos[1] + self.radius, fill=self.color, tags='node')
        tk_label_id = self.canvas.create_text(self.px_pos[0], self.px_pos[1], text=self.node_id, tags='node')
        nm.add_node_to_Graph(self.canvas.root.graph, self.node_id, self.real_pos[0], self.real_pos[1], color=self.color)
        if not nm.node_has_edge(self.canvas.root.graph, self.node_id): nm.create_edges(self.canvas.root.graph, self.node_id)
        self.draw_node_edges(self.canvas.root.graph)
        return tk_node_id, tk_label_id
    
    def get_real_pos_from_px(self, px_pos):
        real_pos = [self.px_pos[0] * 3 / self.canvas.resized_playground_img.width(),
                    self.px_pos[1] * 2 / self.canvas.resized_playground_img.height()]
        return real_pos
    
    def get_px_pos_from_real(self, real_pos):
        px_pos = [real_pos[0] / 3 * self.canvas.resized_playground_img.width(),
                  real_pos[1] / 2 * self.canvas.resized_playground_img.height()]
        return px_pos
    
    def draw_node_edges(self, graph):
        for edge in nm.read_edges(graph, self.node_id):
            dest_node_data = nm.read_node_props(graph, edge[1])
            dest_node_px_pos = self.get_px_pos_from_real((dest_node_data['x'], dest_node_data['y']))
            edge_link = frozenset({edge[1], edge[0]})
            if True and (edge_link not in self.canvas.edges_ids.keys()): # We will have to check here if the connection is possible and if the node is not already connected
                line_id = self.canvas.create_line(self.px_pos[0], self.px_pos[1], dest_node_px_pos[0], dest_node_px_pos[1], fill='black', tags='edge')
                self.canvas.edges_ids[edge_link] = line_id
            elif False and (edge_link in self.canvas.edges_ids.keys()): # Here is if the node is already connected and the connection is not longer possible
                self.canvas.delete(self.edges_ids[edge_link])
                self.canvas.edges_ids.pop(edge_link)
            else: # If the connection is possible but the node is already connected
                # We just update the line geometry
                self.canvas.coords(self.canvas.edges_ids[edge_link], self.px_pos[0], self.px_pos[1], dest_node_px_pos[0], dest_node_px_pos[1])
                
        self.canvas.tag_raise("node")

    def refresh_node_display(self):
        self.canvas.coords(self.tk_node_id, self.px_pos[0] - self.radius, self.px_pos[1] - self.radius, self.px_pos[0] + self.radius, self.px_pos[1] + self.radius)
        self.canvas.coords(self.tk_label_id, self.px_pos[0], self.px_pos[1])
        self.canvas.itemconfig(self.tk_node_id, fill=self.color)
        self.draw_node_edges(self.canvas.root.graph)
    
    def update_node(self, graph):
        new_props = nm.read_node_props(graph, self.node_id)
        self.real_pos = [new_props['x'], new_props['y']]
        self.px_pos = self.get_px_pos_from_real(self.real_pos)
        self.color = new_props['color']
        self.refresh_node_display()
    
    def delete_node(self, graph):
        # Deleting the node and the text label
        self.canvas.delete(self.tk_node_id)
        self.canvas.delete(self.tk_label_id)

        # Deleting the concerned edges
        edges_to_delete = [frozenset(edge) for edge in nm.read_edges(graph, self.node_id)]
        for edge in edges_to_delete:
            self.canvas.delete(self.canvas.edges_ids[edge])
            self.canvas.edges_ids.pop(edge)
        self.canvas.tag_raise("node")

        # Poping out the node from the graph
        self.canvas.node_associated_id.pop(self.tk_node_id)
        nm.delete_node(graph, self.node_id)


class MainToolbar(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.select_tool = tk.Button(self, text='Select', command=self.select)
        self.select_tool.pack(side=tk.LEFT)
        self.select_tool.config(relief=tk.SUNKEN)
        self.place_tool = tk.Button(self, text='Place Nodes', command=self.place)
        self.place_tool.pack(side=tk.LEFT)
        self.link_tool = tk.Button(self, text='Link Nodes', command=self.link)
        self.link_tool.pack(side=tk.LEFT)
        self.delete_tool = tk.Button(self, text='Delete', command=self.delete)
        self.delete_tool.pack(side=tk.LEFT)
        self.buttons = [self.select_tool, self.place_tool, self.link_tool, self.delete_tool]

    def clear_selection(self):
        for button in self.buttons:
            button.config(relief=tk.RAISED)
        self.root.maincanvas.tag_unbind("node","<ButtonPress-1>")
        self.root.maincanvas.tag_unbind("edge","<Button-1>")
        self.root.maincanvas.unbind("<Button-1>")

    def select(self):
        self.clear_selection()
        self.root.maincanvas.tag_bind("node","<ButtonPress-1>",self.root.maincanvas.node_left_cliked)
        self.root.maincanvas.tag_bind("edge","<Button-1>",self.root.maincanvas.edge_left_cliked)
        self.select_tool.config(relief=tk.SUNKEN)
    
    def place(self):
        self.clear_selection()
        self.root.maincanvas.bind("<Button-1>", self.root.maincanvas.playground_left_cliked)
        self.place_tool.config(relief=tk.SUNKEN)

    def link(self):
        self.clear_selection()
        self.link_tool.config(relief=tk.SUNKEN)

    def delete(self):
        self.clear_selection()
        self.delete_tool.config(relief=tk.SUNKEN)




class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, height=20, bd=1, relief=tk.SUNKEN)
        self.parent = parent
        self.status_label = tk.Label(self, text="Ready !")
        self.status_label.pack(side=tk.LEFT)
        self.complexity_label = tk.Label(self, text="Graph Complexity: 0")
        self.complexity_label.pack(side=tk.RIGHT)

    def update_status(self, status):
        self.status_label.config(text=status)
    
    def update_complexity(self, complexity):
        self.complexity_label.config(text="Graph Complexity: " + str(complexity))


class MainCanvas(tk.Canvas):
    def __init__(self, parent, root):
        super().__init__(parent, bg='lightblue')
        self.parent = parent
        self.root = root

        self.node_associated_id = dict() # Links each tkinter node id to a canvas node object
        self.edges_ids = dict() # Links each edge(represented by a set) to a tkinter line id

        self.playground_img = Image.open("images/playground.png")
        self.playground_img_ratio = self.playground_img.size[1] / self.playground_img.size[0]
        self.resized_playground_img = ImageTk.PhotoImage(self.playground_img.resize((int(int(self.cget('width'))), int(int(self.cget('width'))*self.playground_img_ratio))))
        self.canvas_img = self.create_image(int(int(self.cget('width')))/2,
                                            int(int(self.cget('width')))*self.playground_img_ratio/2,
                                            image=self.resized_playground_img,
                                            anchor=tk.CENTER,
                                            tags="playground")
        
        self.last_element_selected = None
        self.last_element_selected = None

        for node in nm.get_nodes(self.root.graph):
            node_obj = Canvas_Node(self, node[0], real_init_x_pos=node[1]['x'], real_init_y_pos=node[1]['y'], color=node[1]['color'])
            self.node_associated_id[int(node_obj.tk_node_id)] = node_obj

        self.bind("<Configure>", self.resize_callback)

        self.bind_all("<KeyPress-Left>", self.left_key_pressed)
        self.bind_all("<KeyPress-Right>", self.right_key_pressed)
        self.bind_all("<KeyPress-Up>", self.up_key_pressed)
        self.bind_all("<KeyPress-Down>", self.down_key_pressed)
        self.bind_all("<KeyPress-Delete>", self.delete_key_pressed)

        self.tag_bind("node","<ButtonPress-1>",self.node_left_cliked)
        self.tag_bind("edge","<Button-1>",self.edge_left_cliked)

    def resize_callback(self, *args):
        if int(int(self.winfo_width()))*self.playground_img_ratio <= int(int(self.winfo_height())):
            self.resized_playground_img = ImageTk.PhotoImage(self.playground_img.resize((int(int(self.winfo_width())), int(int(self.winfo_width())*self.playground_img_ratio))))
            self.coords(self.canvas_img, int(int(self.winfo_width())/2), int(int(self.winfo_width())*self.playground_img_ratio/2))
        else:
            self.resized_playground_img = ImageTk.PhotoImage(self.playground_img.resize((int(int(self.winfo_height())/self.playground_img_ratio), int(int(self.winfo_height())))))
            self.coords(self.canvas_img, int(int(self.winfo_height())/self.playground_img_ratio/2), int(int(self.winfo_height())/2))
        self.itemconfigure(self.canvas_img, image=self.resized_playground_img)
        
        for canvas_node_id in self.node_associated_id.values():
            canvas_node_id.update_node(self.root.graph)

    def node_left_cliked(self, event):
        """
            This Event occurs when the user left clicks on a node.
        """
        # We select the node and not the text label of the node
        node_selected = (self.find_closest(event.x, event.y)[0]) if self.type(self.find_closest(event.x, event.y)[0]) == 'oval' else (self.find_closest(event.x, event.y)[0]-1)

        self.itemconfigure(node_selected, outline='blue', width=3)

        # If the user has already selected a node, we unselect it
        if self.last_element_selected is not None:
            if self.type(self.last_element_selected) == 'line':
                self.itemconfigure(self.last_element_selected, fill="black", width=1)
            else:
                self.itemconfigure(self.last_element_selected, outline="black", width=1)

        self.last_element_selected = node_selected

        # We load selected node proprieties to the the PropertiesTab
        self.root.properties_tab.load_properties(self.node_associated_id[node_selected].node_id)

    def playground_left_cliked(self, event):
        # Draw a new node with a text label
        id = max(int(node.node_id) for node in self.node_associated_id.values())+1 if self.node_associated_id != {} else 1
        node_obj = Canvas_Node(self, id,event.x, event.y)
        self.node_associated_id[node_obj.tk_node_id] = node_obj

        self.node_left_cliked(event)
        self.root.statusbar.update_complexity(nm.number_of_edges(self.root.graph))
    
    def edge_left_cliked(self, event):
        edge_selected = self.find_closest(event.x, event.y)[0]
        self.root.properties_tab.load_properties(None)
        self.itemconfigure(edge_selected, fill='blue', width=3)

        # If the user has already selected an edge, we unselect it
        if self.last_element_selected is not None:
            if self.type(self.last_element_selected) == 'line':
                self.itemconfigure(self.last_element_selected, fill="black", width=1)
            else:
                self.itemconfigure(self.last_element_selected, outline="black", width=1)

        self.last_element_selected = edge_selected

    def left_key_pressed(self, event):
        actual_x_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id)['x']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id, x=actual_x_pos-0.02)
        self.node_associated_id[self.last_element_selected].update_node(self.root.graph)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_element_selected].node_id)
    
    def right_key_pressed(self, event):
        actual_x_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id)['x']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id, x=actual_x_pos+0.02)
        self.node_associated_id[self.last_element_selected].update_node(self.root.graph)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_element_selected].node_id)
    
    def up_key_pressed(self, event):
        actual_y_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id)['y']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id, y=actual_y_pos-0.02)
        self.node_associated_id[self.last_element_selected].update_node(self.root.graph)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_element_selected].node_id)
    
    def down_key_pressed(self, event):
        actual_y_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id)['y']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_element_selected].node_id, y=actual_y_pos+0.02)
        self.node_associated_id[self.last_element_selected].update_node(self.root.graph)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_element_selected].node_id)
    
    def delete_key_pressed(self, event):
        if self.type(self.last_element_selected) == 'line':
            self.root.properties_tab.load_properties(None)
            self.delete_edge(self.root.graph, self.last_element_selected)
        elif self.type(self.last_element_selected) == 'oval':
            self.node_associated_id[self.last_element_selected].delete_node(self.root.graph)
    
    def delete_edge(self, graph, edge_tk_id):
        self.delete(edge_tk_id)
        for key, value in self.edges_ids.items():
            if value == edge_tk_id:
                self.edges_ids.pop(key)
                nm.delete_edge(graph, key)
                break

class ProprietiesTab(tk.LabelFrame):
    def __init__(self, parent, root):
        super().__init__(parent, text="Proprieties")
        self.parent = parent
        self.root = root
        xposLabel = tk.Label(self, text="X Position")
        xposLabel.grid(row=0, column=0)
        self.xposEntry = tk.Entry(self, validatecommand=lambda: self.entry_value_changed("x"), validate="focus")
        self.xposEntry.grid(row=0, column=1)
        yposLabel = tk.Label(self, text="Y Position")
        yposLabel.grid(row=1, column=0)
        self.yposEntry = tk.Entry(self, validatecommand=lambda: self.entry_value_changed("y"), validate="focus")
        self.yposEntry.grid(row=1, column=1)
        descriptionLabel = tk.Label(self, text="Description")
        descriptionLabel.grid(row=2, column=0)
        self.descriptionText = tk.Text(self, height=3, width=20)
        self.descriptionText.grid(row=2, column=1)
        orientationoptionmenuLabel = tk.Label(self, text="Orientation")
        orientationoptionmenuLabel.grid(row=3, column=0)
        defaultstrVar = tk.StringVar()
        defaultstrVar.set("None")
        self.orientationoptionmenu = tk.OptionMenu(self, defaultstrVar,*("North", "South", "East", "West"))
        self.orientationoptionmenu.grid(row=3, column=1)
        self.orientationoptionmenu.config(width=10)
        colorLabel = tk.Label(self, text="Color :")
        colorLabel.grid(row=4, column=0)
        self.colorButton = tk.Button(self, text="Choose Color", command=self.choose_color)
        self.colorButton.grid(row=4, column=1)

        for w in self.winfo_children():
                w.config(state="disabled")

    def entry_value_changed(self, entry_name):
        # A changer c'est horriblement écrit là, valable pour toute cette fonction, tout est horrible...
        if entry_name == "x":
            text = self.xposEntry.get()
        elif entry_name == "y":
            text = self.yposEntry.get()
        try:
            float(text)
            if entry_name == "x":
                nm.write_node_props(self.root.graph, self.root.maincanvas.node_associated_id[self.root.maincanvas.last_element_selected].node_id, x=float(text))
            elif entry_name == "y":
                nm.write_node_props(self.root.graph, self.root.maincanvas.node_associated_id[self.root.maincanvas.last_element_selected].node_id, y=float(text))
            self.root.maincanvas.node_associated_id[self.root.maincanvas.last_element_selected].update_node(self.root.graph)
            return True
        except ValueError:
            return False
    
    def choose_color(self):
        self.color = askcolor('#ff0000', parent=self)
        self.colorButton.config(bg=self.color[1])

        sel_node = self.root.maincanvas.node_associated_id[self.root.maincanvas.last_element_selected]
        nm.write_node_props(self.root.graph, sel_node.node_id, color=self.color[1])

        sel_node.update_node(self.root.graph)

    def load_properties(self, node_id):
        if node_id is None:
            self.xposEntry.delete(0, tk.END)
            self.yposEntry.delete(0, tk.END)
            self.colorButton.config(bg="white")
            for w in self.winfo_children():
                w.config(state="disabled")
            self.root.statusbar.update_status("One node as been deleted")
        else:
            for w in self.winfo_children():
                w.config(state="normal")
            self.root.statusbar.update_status("Editing Node n° " + str(node_id))
            props = nm.read_node_props(self.root.graph, node_id)
            self.xposEntry.delete(0, tk.END)
            self.xposEntry.insert(0, str(props['x']))
            self.yposEntry.delete(0, tk.END)
            self.yposEntry.insert(0, str(props['y']))
            self.colorButton.config(bg=props['color'])


class AboutTopLevel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("About")
        self.geometry("400x190")
        self.resizable(False, False)
        self.config(bg="white")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.canvasthomas = tk.Canvas(self, width=134, height=190, bg="white")
        self.canvasthomas.pack(side=tk.LEFT)
        mixer.init()
        mixer.music.load("sounds/thomas.mp3")
        mixer.music.play()

        thomascanvas = Image.open("images/thomas.png")
        img_ratio = thomascanvas.size[1] / thomascanvas.size[0]
        thomascanvasResized = ImageTk.PhotoImage(thomascanvas.resize((int(190/img_ratio), 190)))
        self.canvas_img = self.canvasthomas.create_image(190/img_ratio/2,
                                            190/2,
                                            image=thomascanvasResized,
                                            anchor=tk.CENTER,
                                            tags="thomas")
        self.left_pupils = self.canvasthomas.create_oval(50, 59, 55, 64, fill="black", tags="thomas")
        self.right_pupils = self.canvasthomas.create_oval(84, 59, 89, 64, fill="black", tags="thomas")

        self.canvasthomas.bind_all("<Motion>", self.update_pupils)
        self.canvasthomas.tag_bind("thomas", "<Button-1>", self.whistle)
        
        self.mainloop()
    
    def whistle(self, event):
        mixer.Channel(0).play(mixer.Sound('sounds/whistle.mp3'), maxtime=2500)

    def update_pupils(self, event):
        left_eye_canvas_pos = 52.5, 61.5
        right_eye_canvas_pos = 81.5, 61.5
        
        # Get the mouse position relative to the widget
        mouse_pos = event.x, event.y

        # Get the mouse position relative to the eyes
        mouse_pos_left = (mouse_pos[0] - left_eye_canvas_pos[0], mouse_pos[1] - left_eye_canvas_pos[1])
        mouse_pos_right = (mouse_pos[0] - right_eye_canvas_pos[0], mouse_pos[1] - right_eye_canvas_pos[1])

        # Get the angle of the mouse relative to the canvas
        angle_left = math.atan2(mouse_pos_left[1], mouse_pos_left[0])
        angle_right = math.atan2(mouse_pos_right[1], mouse_pos_right[0])

        # Move the eyes
        if math.sqrt(mouse_pos_left[0]**2 + mouse_pos_left[1]**2) < 5:
            self.canvasthomas.coords(self.left_pupils, mouse_pos_left[0] + 50, mouse_pos_left[1] + 59, mouse_pos_left[0] + 55, mouse_pos_left[1] + 64)
        else:
            self.canvasthomas.coords(self.left_pupils, 5*math.cos(angle_left) + 50, 5*math.sin(angle_left) + 59, 5*math.cos(angle_left) + 55, 5*math.sin(angle_left) + 64)
        if math.sqrt(mouse_pos_right[0]**2 + mouse_pos_right[1]**2) < 5:
            self.canvasthomas.coords(self.right_pupils, mouse_pos_right[0] + 79, mouse_pos_right[1] + 59, mouse_pos_right[0] + 84, mouse_pos_right[1] + 64)
        else:
            self.canvasthomas.coords(self.right_pupils, 5*math.cos(angle_right) + 79, 5*math.sin(angle_right) + 59, 5*math.cos(angle_right) + 84, 5*math.sin(angle_right) + 64)

    def destroy(self):
        mixer.music.stop()
        self.destroy()


class MenuBar(tk.Menu):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.filemenu = tk.Menu(self, tearoff="off")
        self.add_cascade(label='File', menu=self.filemenu)
        self.filemenu.add_command(label='New file', command=self.new_file)
        self.filemenu.add_command(label='Open file', command=self.open_file)
        self.filemenu.add_command(label='Save file', command=self.save_file)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit', command=self.quit)

        self.editmenu = tk.Menu(self, tearoff="off")
        self.add_cascade(label='Edit', menu=self.editmenu)
        self.editmenu.add_command(label='Undo', command=self.undo)
        self.editmenu.add_command(label='Redo', command=self.redo)

        self.rosmenu = tk.Menu(self, tearoff="off")
        self.add_cascade(label='ROS', menu=self.rosmenu)
        self.rosmenu.add_command(label='Connect to ROS', command=self.connect_to_ros)
        self.rosmenu.add_command(label='Disconnect from ROS', command=self.disconnect_from_ros)

        self.helpmenu = tk.Menu(self, tearoff="off")
        self.add_cascade(label='Help', menu=self.helpmenu)
        self.helpmenu.add_command(label='About', command=self.about)

    def new_file(self):
        newmainApp = MainApplication()
        newmainApp.mainloop()

    def open_file(self):
        filepath = askopenfilename(filetypes=[("Graph Modelling Language File", "*.gml"), ("All files", "*.*")])
        if filepath:
            newmainApp = MainApplication(nm.read_graph(filepath))
            newmainApp.mainloop()

    def save_file(self):
        filepath = asksaveasfilename(defaultextension=".gml", filetypes=[("Graph Modelling Language File", "*.gml"), ("All files", "*.*")])
        if filepath:
            nm.save_graph(self.parent.graph, filepath)

    def undo(self):
        pass

    def redo(self):
        pass

    def connect_to_ros(self):
        pass

    def disconnect_from_ros(self):
        pass
    
    def about(self):
        aboutToplevel = AboutTopLevel(self)


class MainApplication(tk.Toplevel):
    def __init__(self, graph=nm.init_Graph()):
        super().__init__()

        # Setting up basic windows shape and infos
        self.title("NodePla7er - 7Robot")
        self.geometry("700x500")
        self.resizable(True, True)
        self.grid_columnconfigure(index=0, weight=1)
        self.grid_rowconfigure(index=0, weight=1)
        self.iconphoto(True, tk.PhotoImage(file="images/app_icon.png"))
        self.graph = graph
        self.init_ui()

    def init_ui(self):
        self.menubar = MenuBar(self)
        self.config(menu=self.menubar)

        self.toolbar = MainToolbar(self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.workspace_Frame = tk.Frame(self)
        self.workspace_Frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.maincanvas = MainCanvas(self.workspace_Frame, self)
        self.maincanvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.properties_tab = ProprietiesTab(self.workspace_Frame, self)
        self.properties_tab.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.W)

        self.statusbar = StatusBar(self)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)


if __name__ == "__main__":
    primary = tk.Tk()
    # Hide the window
    primary.withdraw()

    # Create the application
    mainApp = MainApplication()
    mainApp.mainloop()