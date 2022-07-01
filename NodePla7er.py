from logging import root
import tkinter as tk
from tkcolorpicker import askcolor
from turtle import color, window_height
from PIL import Image, ImageTk
from cv2 import resize
import filemanager as fm
import networkmanager as nm


class Canvas_Node():
    def __init__(self, canvas, node_id, px_init_x_pos, px_init_y_pos,radius=10, color='red'):
        self.canvas = canvas
        self.node_id = node_id
        self.radius = radius
        self.color = color
        self.real_pos = (0, 0)
        self.px_pos = (0, 0)

        self.tk_node_id, self.tk_label_id = self.create_node(px_init_x_pos, px_init_y_pos)

    def create_node(self, px_init_x_pos, px_init_y_pos):
        self.px_pos = (px_init_x_pos, px_init_y_pos)
        self.real_pos = self.get_real_pos_from_px(self.px_pos)
        tk_node_id = self.canvas.create_oval(self.px_pos[0] - self.radius, self.px_pos[1] - self.radius, self.px_pos[0] + self.radius, self.px_pos[1] + self.radius, self.color)
        tk_label_id = self.canvas.create_text(self.px_pos[0], self.px_pos[1], text=self.node_id)
        return tk_node_id, tk_label_id
    
    def get_real_pos_from_px(self, px_pos):
        self.real_pos[0] = self.px_pos[0] * 3 / self.canvas.resized_playground_img.width() # Change this value to change the scale of the playground
        self.real_pos[1] = self.px_pos[1] * 2 / self.canvas.resized_playground_img.height() # Change this value to change the scale of the playground
        return self.real_pos
    
    def get_px_pos_from_real(self, real_pos):
        self.px_pos[0] = real_pos / 3 * self.canvas.resized_playground_img.width()
        self.px_pos[1] = real_pos / 2 * self.canvas.resized_playground_img.height()
        return self.px_pos
    
    def draw_node_edges(self, graph):
        for edge in nm.read_edges(graph, self.node_id):
            dest_node_data = nm.read_node_props(graph, edge[1])
            dest_node_px_pos = self.get_px_pos_from_real(dest_node_data['x'], dest_node_data['y'])
            edge_link = {edge[1], edge[0]}
            if True and (edge_link not in self.canvas.edges_ids.keys()): # We will have to check here if the connection is possible and if the node is not already connected
                line_id = self.canvas.create_line(self.px_pos[0], self.px_pos[1], dest_node_px_pos[0], dest_node_px_pos[1], fill='black')
                self.canvas.edges_ids[edge_link] = line_id
            elif False and (edge_link in self.canvas.edges_ids.keys()): # Here is if the node is already connected and the connection is not longer possible
                self.canvas.delete(self.edges_ids[edge_link])
                self.canvas.edges_ids.pop(edge_link)
            else: # If the connection is possible but the node is already connected
                # We just update the line geometry
                self.canvas.coords(self.canvas.edges_ids[edge_link], self.px_pos[0], self.px_pos[1], dest_node_px_pos[0], dest_node_px_pos[1])
                
        self.tag_raise("node")

    def refresh_node_display(self):
        self.canvas.coords(self.tk_node_id, self.px_pos[0] - self.radius, self.px_pos[1] - self.radius, self.px_pos[0] + self.radius, self.px_pos[1] + self.radius)
        self.canvas.coords(self.tk_label_id, self.px_pos[0], self.px_pos[1])
        self.canvas.itemconfig(self.tk_node_id, fill=self.color)
        self.canvas.delete("edge")
        self.draw_node_edges(self.canvas.graph)
    
    def update_node(self, graph):
        new_props = graph.get_node_properties(self.node_id)
        


class MainToolbar(tk.Frame):
    def __init__(self):
        super().__init__()


class StatusBar(tk.Frame):
    def __init__(self):
        super().__init__(height=20, bd=1, relief=tk.SUNKEN)
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

        self.node_associated_id = {}

        self.playground_img = Image.open("images/playground.png")
        self.playground_img_ratio = self.playground_img.size[1] / self.playground_img.size[0]
        self.resized_playground_img = ImageTk.PhotoImage(self.playground_img.resize((int(int(self.cget('width'))), int(int(self.cget('width'))*self.playground_img_ratio))))
        self.canvas_img = self.create_image(int(int(self.cget('width')))/2,
                                            int(int(self.cget('width')))*self.playground_img_ratio/2,
                                            image=self.resized_playground_img,
                                            anchor=tk.CENTER,
                                            tags="playground")
        
        self.last_node_selected = None

        self.bind("<Configure>", self.resize_callback)

        self.bind_all("<KeyPress-Left>", self.left_key_pressed)
        self.bind_all("<KeyPress-Right>", self.right_key_pressed)
        self.bind_all("<KeyPress-Up>", self.up_key_pressed)
        self.bind_all("<KeyPress-Down>", self.down_key_pressed)
        
        self.bind_all("<KeyPress-Delete>", self.delete_key_pressed)

        self.tag_bind("node","<Button-1>",self.node_left_cliked)
        self.tag_bind("playground","<Button-1>",self.playground_left_cliked)

    def update_canvas_node(self, canvas_node_id):
        if canvas_node_id is not None:
            props = nm.read_node_props(self.root.graph, self.node_associated_id[canvas_node_id])
            x = props['x'] / 3 * self.resized_playground_img.width() # Change this value to change the scale of the playground
            y = props['y'] / 2 * self.resized_playground_img.height() # Change this value to change the scale of the playground
            self.coords(canvas_node_id, x-10, y-10, x+10, y+10)
            self.coords(canvas_node_id+1, x, y)
            self.itemconfigure(canvas_node_id, fill=props['color'])

        self.delete("edge")
        for canvas_node_id in self.node_associated_id.keys():
            self.draw_edges_from_node(self.node_associated_id[canvas_node_id])        # C'est pas opti je sais...
        self.root.statusbar.update_complexity(nm.number_of_edges(self.root.graph))
    
    def draw_edges_from_node(self, node_id):
        playground_width = self.resized_playground_img.width()
        playground_height = self.resized_playground_img.height()
        origin_node_props = nm.read_node_props(self.root.graph, node_id)
        origin_node_px_pos = origin_node_props['x'] / 3 * playground_width, origin_node_props['y'] / 2 * playground_height
        for edge in nm.read_edges(self.root.graph, node_id):
            dest_node_px_pos = nm.read_node_props(self.root.graph, edge[1])['x'] / 3 * playground_width, nm.read_node_props(self.root.graph, edge[1])['y'] / 2 * playground_height
            self.create_line(origin_node_px_pos, dest_node_px_pos, fill="black", width=1, tags="edge")
        self.tag_raise("node")
    
    def resize_callback(self, *args):
        if int(int(self.winfo_width()))*self.playground_img_ratio <= int(int(self.winfo_height())):
            self.resized_playground_img = ImageTk.PhotoImage(self.playground_img.resize((int(int(self.winfo_width())), int(int(self.winfo_width())*self.playground_img_ratio))))
            self.coords(self.canvas_img, int(int(self.winfo_width())/2), int(int(self.winfo_width())*self.playground_img_ratio/2))
        else:
            self.resized_playground_img = ImageTk.PhotoImage(self.playground_img.resize((int(int(self.winfo_height())/self.playground_img_ratio), int(int(self.winfo_height())))))
            self.coords(self.canvas_img, int(int(self.winfo_height())/self.playground_img_ratio/2), int(int(self.winfo_height())/2))
        self.itemconfigure(self.canvas_img, image=self.resized_playground_img)
        
        for canvas_node_id in self.node_associated_id.keys():
            self.update_canvas_node(canvas_node_id)           # C'est pas opti je sais...
    
    def node_left_cliked(self, event):
        """
            This Event occurs when the user left clicks on a node.
        """
        # We select the node and not the text label of the node
        node_selected = (self.find_closest(event.x, event.y)[0]) if self.type(self.find_closest(event.x, event.y)[0]) == 'oval' else (self.find_closest(event.x, event.y)[0]-1)

        self.itemconfigure(node_selected, outline='blue', width=3)

        # If the user has already selected a node, we unselect it
        if self.last_node_selected is not None:
            self.itemconfigure(self.last_node_selected, outline="black", width=1)

        self.last_node_selected = node_selected

        # We load selected node proprieties to the the PropertiesTab
        self.root.properties_tab.load_properties(self.node_associated_id[node_selected])

    def playground_left_cliked(self, event):
        # Draw a new node with a text label
        tkinter_id = self.create_oval(event.x-10, event.y-10, event.x+10, event.y+10, fill="red", tags="node")
        # Create a new id for the node and save it to a dictionary where the key is the generated id and the value is the canvas associated id 
        id = max(self.node_associated_id.values())+1 if self.node_associated_id != {} else 1
        self.node_associated_id[tkinter_id] = id

        self.create_text(event.x, event.y, text=str(id), tags="node")

        #convert pixel to meter and save data to the graph
        x = event.x * 3 / self.resized_playground_img.width() # Change this value to change the scale of the playground
        y = event.y * 2 / self.resized_playground_img.height() # Change this value to change the scale of the playground
        print(x, y)
        nm.add_node_to_Graph(self.root.graph, id, x, y)
        nm.create_edges(self.root.graph, id)
        self.draw_edges_from_node(id)
        self.node_left_cliked(event)
        self.root.statusbar.update_complexity(nm.number_of_edges(self.root.graph))
    
    def left_key_pressed(self, event):
        actual_x_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_node_selected])['x']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_node_selected], x=actual_x_pos-0.02)
        self.update_canvas_node(self.last_node_selected)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_node_selected])
    
    def right_key_pressed(self, event):
        actual_x_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_node_selected])['x']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_node_selected], x=actual_x_pos+0.02)
        self.update_canvas_node(self.last_node_selected)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_node_selected])
    
    def up_key_pressed(self, event):
        actual_y_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_node_selected])['y']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_node_selected], y=actual_y_pos-0.02)
        self.update_canvas_node(self.last_node_selected)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_node_selected])
    
    def down_key_pressed(self, event):
        actual_y_pos = nm.read_node_props(self.root.graph, self.node_associated_id[self.last_node_selected])['y']
        nm.write_node_props(self.root.graph, self.node_associated_id[self.last_node_selected], y=actual_y_pos+0.02)
        self.update_canvas_node(self.last_node_selected)
        self.root.properties_tab.load_properties(self.node_associated_id[self.last_node_selected])
    
    def delete_key_pressed(self, event):
        self.root.properties_tab.load_properties(None)
        nm.delete_node(self.root.graph, self.node_associated_id[self.last_node_selected])
        self.node_associated_id.pop(self.last_node_selected)
        self.delete(self.last_node_selected)
        self.delete(self.last_node_selected+1)
        self.last_node_selected = None
        self.update_canvas_node(self.last_node_selected)

class ProprietiesTab(tk.LabelFrame):
    def __init__(self, parent, root):
        super().__init__(parent, text="Propriety")
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
        colorLabel = tk.Label(self, text="Color :")
        colorLabel.grid(row=2, column=0)
        self.colorButton = tk.Button(self, text="Choose Color", command=self.choose_color)
        self.colorButton.grid(row=2, column=1)

    def entry_value_changed(self, entry_name):
        # A changer c'est horriblement écrit là, valable pour toute cette fonction, tout est horrible...
        if entry_name == "x":
            text = self.xposEntry.get()
        elif entry_name == "y":
            text = self.yposEntry.get()
        try:
            float(text)
            if entry_name == "x":
                nm.write_node_props(self.root.graph, self.root.maincanvas.node_associated_id[self.root.maincanvas.last_node_selected], x=float(text))
            elif entry_name == "y":
                nm.write_node_props(self.root.graph, self.root.maincanvas.node_associated_id[self.root.maincanvas.last_node_selected], y=float(text))
            self.root.maincanvas.update_canvas_node(self.root.maincanvas.last_node_selected)
            return True
        except ValueError:
            return False
    def choose_color(self):
        self.color = askcolor()
        self.colorButton.config(bg=self.color[1])
        nm.write_node_props(self.root.graph, self.root.maincanvas.node_associated_id[self.root.maincanvas.last_node_selected], color=self.color[1])
        self.root.maincanvas.update_canvas_node(self.root.maincanvas.last_node_selected)

    def load_properties(self, node_id):
        if node_id is None:
            self.xposEntry.delete(0, tk.END)
            self.yposEntry.delete(0, tk.END)
            self.colorButton.config(bg="white")
            self.root.statusbar.update_status("One node as been deleted")
        else:
            self.root.statusbar.update_status("Editing Node n° " + str(node_id))
            props = nm.read_node_props(self.root.graph, node_id)
            self.xposEntry.delete(0, tk.END)
            self.xposEntry.insert(0, str(props['x']))
            self.yposEntry.delete(0, tk.END)
            self.yposEntry.insert(0, str(props['y']))
            self.colorButton.config(bg=props['color'])




class MenuBar(tk.Menu):
    def __init__(self, parent):
        super().__init__(parent)
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
        pass

    def open_file(self):
        pass

    def save_file(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def connect_to_ros(self):
        pass

    def disconnect_from_ros(self):
        pass
    
    def about(self):
        pass


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()

        # Setting up basic windows shape and infos
        self.title("NodePla7er - 7Robot")
        self.geometry("700x500")
        self.resizable(True, True)
        self.grid_columnconfigure(index=0, weight=1)
        self.grid_rowconfigure(index=0, weight=1)
        self.iconphoto(True, tk.PhotoImage(file="images/app_icon.png"))
        self.init_ui()
        self.graph = nm.init_Graph()

    def init_ui(self):
        self.menubar = MenuBar(self)
        self.config(menu=self.menubar)

        self.workspace_Frame = tk.Frame(self)
        self.workspace_Frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.maincanvas = MainCanvas(self.workspace_Frame, self)
        self.maincanvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.properties_tab = ProprietiesTab(self.workspace_Frame, self)
        self.properties_tab.pack(side=tk.LEFT, fill=tk.Y, anchor=tk.W)

        self.statusbar = StatusBar()
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)


if __name__ == "__main__":
    mainApp = MainApplication()
    mainApp.mainloop()