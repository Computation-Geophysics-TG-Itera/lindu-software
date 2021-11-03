import sys
import subprocess
import shutil
import numpy as np
import os
import cv2
from pathlib import Path

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtUiTools import QUiLoader
from tempfile import mkdtemp
from matplotlib.pyplot import imread

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar

class MessageOpt(QMessageBox):
    def __init__(self, title, maintext, opttext):
        QMessageBox.__init__(self)
        self.setWindowTitle(title)
        self.setWindowIcon(self.icon)
        self.setText(maintext)
        self.setInformativeText(opttext)
        self.setIcon(QMessageBox.Information)
        self.setStandardButtons(QMessageBox.Close)

class modelDisplay(QWidget):
    def __init__(self,vel,x,y,parent=None):
        super(modelDisplay, self).__init__(parent)

        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        self.fig.figure = Figure()
        self.fig.canvas = FigureCanvas(self.fig.figure)
        self.fig.toobar = NavigationToolbar(self.fig.canvas, self.fig)
        self.ax1 = self.fig.figure.add_subplot(111)
        self.ax1.set_title('2D Velocity')
        map = self.ax1.imshow(vel, cmap='jet_r', extent=[x.min(), x.max(), y.max(), y.min()])
        clb = self.fig.colorbar(map, orientation='horizontal')
        clb.ax.set_title('vel (km/s)')
        self.fig.tight_layout()
        self.x = []
        self.y = []
        self.points = self.ax1.scatter(self.x, self.y, color='red', picker=20)
        # self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        mainLayout.addWidget(self.fig.figure)
        mainLayout.addWidget(self.fig.toobar)

        # FigureCanvas.__init__(self, self.fig)
        # self.fig.canvas.setParent(parent)
        # FigureCanvas.setSizePolicy(self,
        #                            QSizePolicy.Expanding,
        #                            QSizePolicy.Expanding)
        # FigureCanvas.updateGeometry(self)

    def on_click(self, event):
        if event.inaxes is None:
            return
        else:
            self.x.append(event.xdata)
            self.y.append(event.ydata)
            self.xy = []
            self.xy.append([event.xdata, event.ydata])
            print(event.xdata, event.ydata)
            self.points.set_offsets(self.xy)
            self.ax1.draw_artist(self.points)
            self.fig.canvas.blit(self.ax1.bbox)
            self.fig.canvas.draw()

class initDisplay(FigureCanvas):
    def __init__(self,img,parent=None):

        self.fig = Figure()
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.set_title('Image Display')
        map = self.ax1.imshow(img, cmap='jet_r')
        clb = self.fig.colorbar(map, orientation='horizontal')
        clb.ax.set_title('color value')
        self.fig.tight_layout()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
    
class mainModelDisplay(QMainWindow):
    def __init__(self, figfile, parent = None):
        super(mainModelDisplay, self).__init__(parent)
        self.imgread = imread(figfile)
        self.imgInit = cv2.cvtColor(self.imgread, cv2.COLOR_RGB2GRAY)
        self.mpli = 0
        self.load_ui()
        self.ui_settings()
        self.view_settings()

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent.parent.parent / "ui/tabCreateModel.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file)
        self.setCentralWidget(self.ui)
        self.setGeometry(self.ui.geometry())
        center = QApplication.primaryScreen().availableGeometry().center()
        frameGeom = self.frameGeometry()
        frameGeom.moveCenter(center)
        self.move(frameGeom.topLeft())
        ui_file.close()
    
    def ui_settings(self):
        self.xs = []
        self.ys = []
        self.xys = []
        self.xr = []
        self.yr = []
        self.xyr = []
        self.mpl = 0
        self.isSaved = 0
        self.ui.save_gb.hide()
        self.item_counter = False
        self.ui.model_tree.expandAll()
        self.ui.model_tree.resizeColumnToContents(0)
        self.model_tree_contents()
        self.ui.buttonPickSource.clicked.connect(self.clickButtonPickSource)
        self.ui.buttonPickStation.clicked.connect(self.clickButtonPickStat)
        self.ui.buttonSave.clicked.connect(self.clickButtonSave)
        self.ui.buttonSource.clicked.connect(self.clickButtonSource)
        self.ui.buttonStat.clicked.connect(self.clickButtonStat)
        self.ui.buttonVel.clicked.connect(self.clickButtonVel2d)
        self.ui.model_tree.itemDoubleClicked.connect(lambda item, column: self.tree_double_clicked(item, column))
        self.ui.model_tree.itemChanged.connect(lambda item, column: self.tree_item_changed(item, column))
        self.ui.save_expandbutton.clicked.connect(lambda: self.ui.save_gb.hide() if self.ui.save_gb.isVisible() else self.ui.save_gb.show())
        self.ui.save_expandbutton.clicked.connect(lambda: self.ui.save_expandbutton.setArrowType(Qt.UpArrow) if self.ui.save_gb.isVisible() else self.ui.save_expandbutton.setArrowType(Qt.RightArrow))

    def model_tree_contents(self):
        self.fn_model_tree_find = lambda text: self.ui.model_tree.findItems(text, Qt.MatchExactly | Qt.MatchRecursive, 0)[0]
        item = self.fn_model_tree_find("Unit Color")
        self.unit_color = "unitless"
        item.setText(1, self.unit_color)
        item = self.fn_model_tree_find("Min Color")
        self.min_color = np.min(self.imgInit)
        item.setText(1, str(self.min_color))
        item = self.fn_model_tree_find("Max Color")
        self.max_color = np.max(self.imgInit)
        item.setText(1, str(self.max_color))
        item = self.fn_model_tree_find("X Grid Number")
        self.x_grid = self.imgInit.shape[1]
        item.setText(1, str(self.x_grid))
        item = self.fn_model_tree_find("Z Grid Number")
        self.z_grid = self.imgInit.shape[0]
        item.setText(1, str(self.z_grid))
        item = self.fn_model_tree_find("X Min")
        self.x_min = 0.
        item.setText(1, str(self.x_min))
        item = self.fn_model_tree_find("Z Min")
        self.z_min = 0.
        item.setText(1, str(self.z_min))
        item = self.fn_model_tree_find("X Max")
        self.x_max = float(self.imgInit.shape[1])
        item.setText(1, str(self.x_max))
        item = self.fn_model_tree_find("Z Max")
        self.z_max = float(self.imgInit.shape[0])
        item.setText(1, str(self.z_max))
        self.xline = np.linspace(self.x_min,self.x_max,self.x_grid)
        self.zline = np.linspace(self.z_min,self.z_max,self.z_grid)

    
    def tree_double_clicked(self, item, column):
        if column == 1:
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.ui.model_tree.editItem(item, column)
            self.item_counter = True
            self.prev_name = item.text(column)
    
    def tree_item_changed(self, item, column):
        if self.item_counter == True and self.prev_name != item.text(column):
            self.view_changed(item)
            self.item_counter = False
    
    def view_settings(self):
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui.layoutViewGroupBox.addWidget(self.canvas)
        self.ui.layoutViewGroupBox.addWidget(self.toolbar)

        self.ax = self.figure.add_subplot(111)
        map = self.ax.imshow(self.imgInit, cmap='jet_r')

        clb = self.figure.colorbar(map, orientation='horizontal')
        clb.ax.set_title('Image Color (' + self.unit_color + ')')
        self.figure.tight_layout()

    def view_changed(self, item):
        if item.text(0) == "Unit Color":
            self.unit_color = item.text(1)
        elif item.text(0) == "Min Color":
            self.min_color = int(item.text(1))
        elif item.text(0) == "Max Color":
            self.max_color = int(item.text(1))
        elif item.text(0) == "X Grid Number":
            self.x_grid = int(item.text(1))
        elif item.text(0) == "Z Grid Number":
            self.z_grid = int(item.text(1))
        elif item.text(0) == "X Min":
            self.x_min = float(item.text(1))
        elif item.text(0) == "X Max":
            self.x_max = float(item.text(1))
        elif item.text(0) == "Z Min":
            self.z_min = float(item.text(1))
        elif item.text(0) == "Z Max":
            self.z_max = float(item.text(1))
        
        if item.text(0) != "Unit Color":
            self.xline = np.linspace(self.x_min,self.x_max,self.x_grid)
            self.zline = np.linspace(self.z_min,self.z_max,self.z_grid)
            self.imgInit = cv2.cvtColor(self.imgread, cv2.COLOR_RGB2GRAY)
            img = cv2.resize(self.imgInit, dsize=(self.x_grid, self.z_grid), interpolation=cv2.INTER_CUBIC)
            vel = np.zeros(self.imgInit.shape)

            if np.min(img) != np.max(img):
                vel = (((self.max_color-self.min_color)/(np.max(img)-np.min(img)))*(img-np.min(img)))+self.min_color
            else:
                vel = np.ones(img.shape)*self.min_color
            
            self.imgInit = vel
        
        self.xs = []
        self.ys = []
        self.xys = []
        self.xr = []
        self.yr = []
        self.xyr = []

        fig = Figure()
        can = FigureCanvas(fig)
        tbr = NavigationToolbar(can, self)
        self.ui.layoutViewGroupBox.replaceWidget(self.canvas, can)
        self.ui.layoutViewGroupBox.replaceWidget(self.toolbar, tbr)

        self.figure = fig
        self.canvas = can
        self.toolbar = tbr

        self.ax = self.figure.add_subplot(111)
        map = self.ax.imshow(self.imgInit, cmap='jet_r', extent=[self.x_min, self.x_max, self.z_min, self.z_max])

        clb = self.figure.colorbar(map, orientation='horizontal')
        clb.ax.set_title('velocity (' + self.unit_color + ')')
        self.figure.tight_layout()
    
    def clickButtonPickSource(self):
        if self.mpl == 1:
            self.canvas.mpl_disconnect(self.cid)
        self.mpl = 1
        self.points = self.ax.scatter([], [], s=30, marker='*', linewidths=1, color='red', picker=20)
        self.cid = self.canvas.mpl_connect('button_press_event', self.on_clickSource)

    def clickButtonPickStat(self):
        if self.mpl == 1:
            self.canvas.mpl_disconnect(self.cid)
        self.mpl = 1
        self.points = self.ax.scatter([], [], s=30, marker='v', linewidths=1, color='white', picker=20)
        self.cid = self.canvas.mpl_connect('button_press_event', self.on_clickStat)

    def on_clickSource(self, event):
        if event.inaxes is None:
            return
        else:
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)
            self.xys.append([event.xdata, event.ydata])
            self.points.set_offsets(self.xys)
            self.ax.draw_artist(self.points)
            self.canvas.blit(self.ax.bbox)
            self.canvas.draw()

    def on_clickStat(self, event):
        if event.inaxes is None:
            return
        else:
            self.xr.append(event.xdata)
            self.yr.append(event.ydata)
            self.xyr.append([event.xdata, event.ydata])
            self.points.set_offsets(self.xyr)
            self.ax.draw_artist(self.points)
            self.canvas.blit(self.ax.bbox)
            self.canvas.draw()
    
    def clickButtonSource(self):
        open = QFileDialog()
        filepath = open.getSaveFileName(self, 'Save source file', '/', "Format File (*.src *.dat)")
        self.ui.lineSource.setText(filepath[0])

    def clickButtonStat(self):
        open = QFileDialog()
        filepath = open.getSaveFileName(self, 'Save station file', '/', "Format File (*.stat *.dat)")
        self.ui.lineStat.setText(filepath[0])

    def clickButtonVel2d(self):
        open = QFileDialog()
        filepath = open.getSaveFileName(self, 'Save 2D velocity file', '/', "Format File (*.vel2d)")
        self.ui.lineVel2d.setText(filepath[0])
    
    def clickButtonSave(self):
        if self.ui.lineVel2d.text() != '':
            tempfile = os.path.join(mkdtemp(),'file.npz')
            np.savez(tempfile, vel=self.imgInit, x=self.xline, y=self.zline)
            shutil.copyfile(tempfile,self.ui.lineVel2d.text())
            self.isSaved = 1

        if self.ui.lineSource.text() != '' and self.xs != []:
            file = open(self.ui.lineSource.text(),'w')
            for i in range(len(self.xs)):
                file.write(
                    'SRC'+str(i+1)+'\t'+str(self.xs[i])+'\t'+str(self.ys[i])+'\n'
                )
            file.close()
            self.isSaved = 1

        if self.ui.lineStat.text() != '' and self.xr != []:
            file = open(self.ui.lineStat.text(),'w')
            for i in range(len(self.xr)):
                file.write(
                    'ST'+str(i+1)+'\t'+str(self.xr[i])+'\t'+str(self.yr[i])+'\n'
                )
            file.close()
            self.isSaved = 1

        if self.isSaved != 0:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setText("Save is completed.")
            msg.setWindowTitle("Information")
            msg.show()    
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Check the input, maybe the path is empty")
            msg.setWindowTitle("Warning")
            msg.show()
        
        self.isSaved = 0
        

class mainModelDisplay2(QWidget):
    def __init__(self, figfile, parent = None):
        super(mainModelDisplay2, self).__init__(parent)
        img = imread(figfile)
        self.imgInit = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        self.mpli = 0

        self.setMainWidget()

    def setMainWidget(self):
        # main layout
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)

        # main groupbox
        self.mainGroupBox = QGroupBox()
        self.mainGroupBox.setTitle('Settings')
        self.mainGroupBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMainGroupBox()
        self.mainLayout.addWidget(self.mainGroupBox)

        self.viewGroupBox = QGroupBox()
        self.viewGroupBox.setTitle('View')
        self.setViewGroupBox()
        self.mainLayout.addWidget(self.viewGroupBox)

    def setViewGroupBox(self):
        self.layoutViewGroupBox = QVBoxLayout()
        self.viewGroupBox.setLayout(self.layoutViewGroupBox)
        self.disp = QDialog()
        self.disp.figure = Figure()
        self.disp.canvas = FigureCanvas(self.disp.figure)
        self.disp.tbr = NavigationToolbar(self.disp.canvas, self.disp)
        self.ax1 = self.disp.figure.add_subplot(111)
        self.ax1.set_title('Image Display')
        map = self.ax1.imshow(self.imgInit, cmap='jet_r')
        clb = self.disp.figure.colorbar(map, orientation='horizontal')
        clb.ax.set_title('Image Color')
        self.disp.figure.tight_layout()
        self.layoutViewGroupBox.addWidget(self.disp.canvas)
        self.layoutViewGroupBox.addWidget(self.disp.tbr)

    def setMainGroupBox(self):
        # main layout
        layoutMainGroupBox = QVBoxLayout()
        self.mainGroupBox.setLayout(layoutMainGroupBox)

        # build group of output data
        groupOutputData = QGroupBox()
        groupOutputData.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        groupOutputData.setTitle('Path of Output Data')
        layoutOutputData = QFormLayout()

        # -> filled
        self.lineSource = QLineEdit()
        self.lineSource.setPlaceholderText('Source (*.src) path')
        self.lineStat = QLineEdit()
        self.lineStat.setPlaceholderText('Station (*.stat) path')
        self.lineVel2d = QLineEdit()
        self.lineVel2d.setPlaceholderText('2D Velocity (*.vel2d) path')

        buttonSource = QPushButton()
        buttonSource.setText('...')
        buttonSource.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buttonSource.clicked.connect(self.clickButtonSource)
        buttonStat = QPushButton()
        buttonStat.setText('...')
        buttonStat.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buttonStat.clicked.connect(self.clickButtonStat)
        buttonVel2d = QPushButton()
        buttonVel2d.setText('...')
        buttonVel2d.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buttonVel2d.clicked.connect(self.clickButtonVel2d)

        # -> settings to layout
        layoutOutputData.addRow(self.lineSource, buttonSource)
        layoutOutputData.addRow(self.lineStat, buttonStat)
        layoutOutputData.addRow(self.lineVel2d, buttonVel2d)
        groupOutputData.setLayout(layoutOutputData)
        layoutMainGroupBox.addWidget(groupOutputData)

        # build group of parameter
        groupParameter = QGroupBox()
        groupParameter.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        groupParameter.setTitle('Parameters')
        layoutParameter = QFormLayout()

        # -> filled
        lb_vmin = QLabel()
        lb_vmin.setText('Color Min Value')
        self.vmin = QLineEdit()

        lb_vmax = QLabel()
        lb_vmax.setText('Color Max Value')
        self.vmax = QLineEdit()

        lb_nx = QLabel()
        lb_nx.setText('X Grid Number')
        self.nx = QLineEdit()

        lb_ny = QLabel()
        lb_ny.setText('Z Grid Number')
        self.ny = QLineEdit()

        lb_xmin = QLabel()
        lb_xmin.setText('X Min Value')
        self.xmin = QLineEdit()

        lb_xmax = QLabel()
        lb_xmax.setText('X Max Value')
        self.xmax = QLineEdit()

        lb_ymin = QLabel()
        lb_ymin.setText('Z Min Value')
        self.ymin = QLineEdit()

        lb_ymax = QLabel()
        lb_ymax.setText('Z Max Value')
        self.ymax = QLineEdit()

        # -> settings to layout
        layoutParameter.addRow(lb_vmin, self.vmin)
        layoutParameter.addRow(lb_vmax, self.vmax)
        layoutParameter.addRow(lb_nx, self.nx)
        layoutParameter.addRow(lb_ny, self.ny)
        layoutParameter.addRow(lb_xmin, self.xmin)
        layoutParameter.addRow(lb_xmax, self.xmax)
        layoutParameter.addRow(lb_ymin, self.ymin)
        layoutParameter.addRow(lb_ymax, self.ymax)
        groupParameter.setLayout(layoutParameter)
        layoutMainGroupBox.addWidget(groupParameter)

        # button
        buttonExecute = QPushButton()
        buttonExecute.setText('Execute')
        buttonExecute.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buttonExecute.clicked.connect(self.clickButtonExecute)

        buttonPickSource = QPushButton()
        buttonPickSource.setText('Pick Source')
        buttonPickSource.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buttonPickSource.clicked.connect(self.clickButtonPickSource)

        buttonPickStat = QPushButton()
        buttonPickStat.setText('Pick Station')
        buttonPickStat.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buttonPickStat.clicked.connect(self.clickButtonPickStat)

        buttonSave = QPushButton()
        buttonSave.setText('Save')
        buttonSave.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        buttonSave.clicked.connect(self.clickButtonSave)

        # -> settings to layout
        layoutMainGroupBox.addWidget(buttonExecute)
        layoutMainGroupBox.addWidget(buttonPickStat)
        layoutMainGroupBox.addWidget(buttonPickSource)
        layoutMainGroupBox.addWidget(buttonSave)

    def clickButtonExecute(self):
        self.xs = []
        self.ys = []
        self.xys = []
        self.xr = []
        self.yr = []
        self.xyr = []
        self.layoutViewGroupBox.removeWidget(self.disp.canvas)
        self.layoutViewGroupBox.removeWidget(self.disp.tbr)
        del self.disp.canvas
        del self.disp.tbr
        self.disp.canvas = None
        self.disp.tbr = None

        nx = int(self.nx.text())
        ny = int(self.ny.text())

        x = np.linspace(float(self.xmin.text()),float(self.xmax.text()),nx)
        y = np.linspace(float(self.ymin.text()),float(self.ymax.text()),ny)

        self.xline = x
        self.yline = y

        vmin = float(self.vmin.text())
        vmax = float(self.vmax.text())

        img = cv2.resize(self.imgInit, dsize=(nx, ny), interpolation=cv2.INTER_CUBIC)
        vel = np.zeros(img.shape)

        if np.min(img) != np.max(img):
            for i in range(len(img[:,0])):
                for j in range(len(img[0,:])):
                    vel[i,j] = (((vmax-vmin)/(np.max(img)-np.min(img)))*(img[i,j]-np.min(img)))+vmin
        else:
            vel = np.ones(img.shape)*vmin

        self.vel = vel

        self.disp = QDialog()
        self.disp.figure = Figure()
        self.disp.canvas = FigureCanvas(self.disp.figure)
        self.disp.tbr = NavigationToolbar(self.disp.canvas, self.disp)
        self.ax1 = self.disp.figure.add_subplot(111)
        self.ax1.set_title('2D Velocity')
        map = self.ax1.imshow(vel, cmap='jet_r', extent=[x.min(), x.max(), y.max(), y.min()])
        clb = self.disp.figure.colorbar(map, orientation='horizontal')
        clb.ax.set_title('vel (km/s)')
        self.disp.figure.tight_layout()

        self.layoutViewGroupBox.addWidget(self.disp.canvas)
        self.layoutViewGroupBox.addWidget(self.disp.tbr)



    def clickButtonSource(self):
        open = QFileDialog()
        filepath = open.getSaveFileName(self, 'Save source file', '/', "Format File (*.src *.dat)")
        self.lineSource.setText(filepath[0])

    def clickButtonStat(self):
        open = QFileDialog()
        filepath = open.getSaveFileName(self, 'Save station file', '/', "Format File (*.stat *.dat)")
        self.lineStat.setText(filepath[0])

    def clickButtonVel2d(self):
        open = QFileDialog()
        filepath = open.getSaveFileName(self, 'Save 2D velocity file', '/', "Format File (*.vel2d)")
        self.lineVel2d.setText(filepath[0])

    def clickButtonPickSource(self):
        if self.mpli == 1:
            self.disp.canvas.mpl_disconnect(self.cid)
        # self.xs = []
        # self.ys = []
        # self.xys = []
        self.mpli = 1
        self.points = self.ax1.scatter(self.xs, self.ys, s=30, marker='*', linewidths=1, color='red', picker=20)
        self.cid = self.disp.canvas.mpl_connect('button_press_event', self.on_clickSource)

    def clickButtonPickStat(self):
        if self.mpli == 1:
            self.disp.canvas.mpl_disconnect(self.cid)
        # self.xr = []
        # self.yr = []
        # self.xyr = []
        self.mpli = 1
        self.points = self.ax1.scatter([], [], s=30, marker='v', linewidths=1, color='white', picker=20)
        self.cid = self.disp.canvas.mpl_connect('button_press_event', self.on_clickStat)

    def on_clickSource(self, event):
        if event.inaxes is None:
            return
        else:
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)
            # self.xy = []
            self.xys.append([event.xdata, event.ydata])
            self.points.set_offsets(self.xys)
            self.ax1.draw_artist(self.points)
            self.disp.canvas.blit(self.ax1.bbox)
            self.disp.canvas.draw()

    def on_clickStat(self, event):
        if event.inaxes is None:
            return
        else:
            self.xr.append(event.xdata)
            self.yr.append(event.ydata)
            # self.xy = []
            self.xyr.append([event.xdata, event.ydata])
            self.points.set_offsets(self.xyr)
            self.ax1.draw_artist(self.points)
            self.disp.canvas.blit(self.ax1.bbox)
            self.disp.canvas.draw()

    def clickButtonSave(self):
        if self.lineVel2d.text() != '' or (self.lineStat.text() != '' or self.lineSource != ''):
            if self.lineVel2d.text() != '':
                tempfile = os.path.join(mkdtemp(),'file.npz')
                np.savez(tempfile, vel=self.vel, x=self.xline, y=self.yline)
                shutil.copyfile(tempfile,self.lineVel2d.text())

            if self.lineSource.text() != '':
                file = open(self.lineSource.text(),'w')
                for i in range(len(self.xs)):
                    file.write(
                        'SRC'+str(i+1)+'\t'+str(self.xs[i])+'\t'+str(self.ys[i])+'\n'
                    )
                file.close()

            if self.lineStat.text() != '':
                file = open(self.lineStat.text(),'w')
                for i in range(len(self.xr)):
                    file.write(
                        'ST'+str(i+1)+'\t'+str(self.xr[i])+'\t'+str(self.yr[i])+'\n'
                    )
                file.close()

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setText("Save is completed.")
            msg.setWindowTitle("Information")
            msg.show()    

        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Check the input, maybe the path is empty")
            msg.setWindowTitle("Warning")
            msg.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    figfile = "C:\\Users\\Lenovo\\Pictures\\test_model.jpg"
    main = mainModelDisplay(figfile)
    main.show()
    sys.exit(app.exec_())

