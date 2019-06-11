#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import gimp, gimpplugin, math, array
from gimpenums import *
pdb = gimp.pdb
import gtk, gimpui, gimpcolor
from gimpshelf import shelf
import numpy as np

class lbp_plugin(gimpplugin.plugin):
    shelfkey = "lbp_plugin"
    default_gradient = "LBP"
    layer = None
    
    def start(self):
        gimp.main(self.init, self.quit, self.query, self._run)

    def init(self):
        pass

    def quit(self):
        pass

    def query(self):
        gimp.install_procedure(
            "lbp_main",
            "LBP",
            "Plugin pro LBP.",
            "Petra Svickova",
            "Petra Svickova",
            "2018",
            "<Image>/_Xtns/LBP",
            "GRAY",
            PLUGIN,
            [
                #next three parameters are common for all scripts that are inherited from gimpplugin.plugin
                (PDB_INT32, "run_mode", "Run mode"),
                (PDB_IMAGE, "image", "Input image"),
                (PDB_DRAWABLE, "drawable", "Input drawable"),
                #plugin specific parameters
                (PDB_INT32, "radius", "Radius")
            ],
            []
        )

    def create_dialog(self):
        self.dialog = gimpui.Dialog("LBP", "lbp_dialog")
        
        #3x2 non-homogenous table
        self.table = gtk.Table(3, 2, False)
        self.table.set_row_spacings(8)
        self.table.set_col_spacings(8)
        self.table.show()

        #create label for radius
        rad = 1
        self.label = gtk.Label("Radius: ")
        self.label.set_alignment(0.5, 0.5)
        self.label.show()
        self.table.attach(self.label, 1, 2, 0, 1)

        #create button for radius
        adjustmentRadius = gtk.Adjustment(self.radius, 1, 8, 1)
        self.rad = gtk.SpinButton(adjustmentRadius, rad)
        self.rad.show()
        self.rad.connect("value-changed", self.spin)
        self.table.attach(self.rad, 2, 3, 0, 1)
       
        #dialog inner frames
        #there is a table inside a hbox inside a vbox
        self.dialog.vbox.hbox1 = gtk.HBox(False, 7)
        self.dialog.vbox.hbox1.show()
        self.dialog.vbox.pack_start(self.dialog.vbox.hbox1, True, True, 7)
        self.dialog.vbox.hbox1.pack_start(self.table, True, True, 7)
        
        #buttons at the bottom
        #Ok and Cancel
        if gtk.alternative_dialog_button_order():
            self.ok_button = self.dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            self.cancel_button = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        else:
            self.cancel_button = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            self.ok_button = self.dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.ok_button.connect("clicked", self.ok_clicked)

    def LBP(self):
        width = self.drawable.width
        height = self.drawable.height
        #bpp = self.drawable.bpp
        rad = self.radius

        #debugging messages
        #print("Velikost obrazku: " + str(width) + "x" + str(height))

        #create new output layer
        self.layer = gimp.Layer(self.image, "LBP", width, height, GRAY_IMAGE, 100, NORMAL_MODE)
        #add layer into image
        self.image.add_layer(self.layer, 0)

        #region for output
        dest_rgn = self.layer.get_pixel_rgn(0, 0, width, height, True, True)
        #custom array for results
        drawTo = array.array("B")
   
        #get image data (region) and convert to array 
        imageArr = self.drawable.get_pixel_rgn(0, 0, width, height, False, False)
        imageArr_pixels = array.array("B", imageArr[0:width, 0:height])
        
        #convert 1D array to 2D array
        tmp = np.reshape(imageArr_pixels, (-1, width))

        #create array with mirrored border
        dataBorder = np.pad(array=tmp, pad_width=rad, mode='symmetric')
    
        gimp.progress_init("LBP")
        for x in range(rad,height+rad):
            for y in range(rad,width+rad):
                binaryNum = []

                #get exactly eight pixels in radius from pixel [x,y]                         
                src_pixels = dataBorder[x-rad:x+1+rad:rad, y-rad:y+1+rad:rad]                
                src_pixels = src_pixels.ravel() #make 2D array 1D 
                
                #get value of the center pixel [x,y]
                center = src_pixels[4]
                #sequence of indexes
                indexesNeeded = [0,1,2,5,8,7,6,3]
                
                for i in indexesNeeded:
                    if src_pixels[i] > center:       
                        binaryNum.append(0) 
                    else:       
                        binaryNum.append(1) 

                #"count" LBP for pixel
                st = ''.join(format(str(x)) for x in binaryNum)
                res = int(st,2)

                drawTo.append(res)
  
            gimp.progress_update(float(x+1)/height)
        
        #result
        dest_rgn[0:width, 0:height] = drawTo.tostring()

        #apply changes
        self.layer.flush()
        #apply selection mask
        self.layer.merge_shadow(True)
        #refresh
        self.layer.update(0, 0, width, height)
        #refresh
        gimp.displays_flush()
        

    def ok_clicked(self, widget):
        self.LBP()

    def spin(self,widget):
        self.radius = self.rad.get_value_as_int()

    def lbp_main(self, run_mode, image, drawable, radius = 1, rad = 1):
        #self.rad = rad
        self.radius = radius
        self.drawable = drawable
        self.image = image
        self.create_dialog()
        self.dialog.run()
        gimp.displays_flush()


if __name__ == '__main__':
    lbp_plugin().start()
