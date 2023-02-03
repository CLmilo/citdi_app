import tkinter
import customtkinter


print("Este es otro cambio")
# Main application    
class App(customtkinter.CTk):

    def __init__(self):
        super().__init__()
                    
        #container to pack different windows of the app into
        container = customtkinter.CTkFrame(self)
        container.pack(expand=True, fill='both')
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
    
        self.frames = {}
        self.frames['homescreen'] = HomeScreen(container, self)
        self.frames['page_1'] = MainModes(container, self)
           
        for F in ('homescreen', 'page_1'):
        
            self.frames[F].grid(row = 0, column = 0, sticky='nsew')
    
        self.show_frame('homescreen')
    
    def show_frame(self, page_class):
        frame = self.frames[page_class]
        frame.tkraise()
     
class HomeScreen(customtkinter.CTkFrame):
    def __init__(self, parent, controller):
        customtkinter.CTkFrame.__init__(self, parent)
            
        self.controller = controller
            
        #Configure rows and columns
        self.grid_rowconfigure(0, weight=1) 
        self.grid_rowconfigure(1, weight=1)
                    
        #Define buttons
        page_1_button = customtkinter.CTkButton(self,                                                 
                                                text="Page 1",
                                                command=lambda: controller.show_frame('page_1'))

        #Position of buttons in the main_window
        page_1_button.grid(row=0, column=0, sticky='nsew')
    
class MainModes(customtkinter.CTkFrame):
    def __init__(self, parent, controller):
        customtkinter.CTkFrame.__init__(self, parent)
    
        self.controller = controller

        #overall layout
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1) #mode_1 and mode_2 tabs are contained here
        self.grid_rowconfigure(1, weight=1) #all widgets are contained in two frames in this row, clicking between mode_1 and mode_2 buttons raises different frames containing different widgets
        self.grid_rowconfigure(2, weight=1) #back button is here
           
        self.frame = customtkinter.CTkFrame(self) #this frame contains the mode_1 and mode_2 frames and they are raised over one another according to which tab is selected
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
    
        #====================================Mode 1 Frame====================================#
    
        self.mode_1_frame = customtkinter.CTkFrame(self.frame)
                                                              
        self.mode_1_frame.grid_columnconfigure(0, weight=1)
        self.mode_1_frame.grid_rowconfigure(0, weight=1)
    
        self.mode_1_frame.grid(row=0, column=0, sticky='nsew')               
    
        #====================================Mode 2 Frame====================================# 
    
        self.mode_2_frame = customtkinter.CTkFrame(self.frame)
                                                           
        self.mode_2_frame.grid_columnconfigure(0, weight=1)
        self.mode_2_frame.grid_rowconfigure(0, weight=1)
    
        self.mode_2_frame.grid(row=0, column=0, sticky='nsew')
    
        #====================================Mode 1 Frame Widgets====================================#
                
        self.mode_1_switch_var = tkinter.StringVar(self.mode_1_frame)
        self.mode_1_switch_var.set(value='Mode 1: ON')
    
        #function that sets the textvariable values of mode_1_switch and mode_2_switch when either is toggled
        def switch_functions(switch_var, mode, switch):
            switch_var.set(value=f'{mode}: ' + switch.get())
                                              
        self.mode_1_switch = customtkinter.CTkSwitch(self.mode_1_frame,
                                                 textvariable=self.mode_1_switch_var,
                                                 onvalue='ON',
                                                 offvalue='OFF',
                                                 command=lambda: [switch_functions(self.mode_1_switch_var, 'Mode 1', self.mode_1_switch), self.mode_2_switch.toggle()])
    
        self.mode_1_switch.select()#turns switch on at open
        self.mode_1_switch.grid(row=0, column=0)          
         
        #====================================Mode_2 Frame Widgets====================================# 
               
        self.mode_2_switch_var = tkinter.StringVar(self.mode_2_frame)
        self.mode_2_switch_var.set(value='Mode 2: OFF')
    
                
        self.mode_2_switch = customtkinter.CTkSwitch(self.mode_2_frame,
                                                 textvariable=self.mode_2_switch_var,
                                                 onvalue='ON',
                                                 offvalue='OFF',
                                                 command=lambda: [switch_functions(self.mode_2_switch_var, 'Mode 2', self.mode_2_switch), self.mode_1_switch.toggle()])
     
        self.mode_2_switch.grid(row=0, column=0)
   
        #====================================Frame toggle and back buttons====================================#  
     
        self.mode_2_button = customtkinter.CTkButton(self,
                                                 text='Mode 2',
                                                 command=lambda: self.mode_2_frame.tkraise()) 
    
        self.mode_1_button = customtkinter.CTkButton(self,
                                                 text = 'Mode 1',
                                                 command=lambda: self.mode_1_frame.tkraise())
    
        self.back_button = customtkinter.CTkButton(self,
                                               text='Back',
                                               command=lambda: controller.show_frame('homescreen'))
                     
        self.mode_1_button.grid(row=0, column=0, sticky='nsew')
        self.mode_2_button.grid(row=0, column=1, sticky='nsew')
        self.frame.grid(row=1, columnspan=2, sticky='nsew')
        self.back_button.grid(row=2, column=0, columnspan=2, sticky='nsew')   
    
        self.mode_1_frame.tkraise()

if __name__ == '__main__':
    app = App()
    app.mainloop()
