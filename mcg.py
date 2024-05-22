from pathlib import Path
import itk.itkMedianImageFilterPython
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkRenderingUI
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkCommonDataModel import vtkPlane
from vtkmodules.vtkFiltersCore import (
    vtkClipPolyData
)
from vtkmodules.vtkInteractionWidgets import (
    vtkImplicitPlaneRepresentation,
    vtkImplicitPlaneWidget2
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
from vtk import (
    vtkMarchingCubes,
    vtkConnectivityFilter
)

import itk
from itk.itkMedianImageFilterPython import median_image_filter
from itk.itkDiscreteGaussianImageFilterPython import discrete_gaussian_image_filter

filepath = "./data/imaging.nii"

# Read the data
image = itk.imread(filepath)

# Filter the data
filtered_image = median_image_filter(image, radius=2)
filtered_image = discrete_gaussian_image_filter(filtered_image, variance=1)

# itk image to vtk image
image = itk.vtk_image_from_image(filtered_image)

# vtk image to vtk polydata
marching_cubes = vtkMarchingCubes()
marching_cubes.SetInputData(image)
marching_cubes.SetValue(0, 135)
marching_cubes.Update()

# Region extraction
connectivity_filter = vtkConnectivityFilter()
connectivity_filter.SetInputData(marching_cubes.GetOutput())
connectivity_filter.SetExtractionModeToLargestRegion()
connectivity_filter.Update()

# Setup a visualization pipeline
class IPWCallback:
    def __init__(self, plane):
        self.plane = plane

    def __call__(self, caller, ev):
        rep = caller.GetRepresentation()
        rep.GetPlane(self.plane)


plane = vtkPlane()
plane.SetNormal(1, 0, 0)

clipper = vtkClipPolyData()
clipper.SetClipFunction(plane)
clipper.SetInputConnection(connectivity_filter.GetOutputPort())

# Create a mapper and actor
mapper = vtkPolyDataMapper()
mapper.SetInputConnection(clipper.GetOutputPort())
actor = vtkActor()
actor.SetMapper(mapper)

# A renderer and render window
renderer = vtkRenderer()
ren_win = vtkRenderWindow()
ren_win.AddRenderer(renderer)

colors = vtkNamedColors()
renderer.AddActor(actor)
renderer.SetBackground(colors.GetColor3d("SlateGray"))

# An interactor
iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(ren_win)

# The callback will do the work
my_callback = IPWCallback(plane=plane)

rep = vtkImplicitPlaneRepresentation()
rep.SetPlaceFactor(1.25)
rep.PlaceWidget(actor.GetBounds())
rep.SetNormal(plane.GetNormal())

plane_widget = vtkImplicitPlaneWidget2()
plane_widget.SetInteractor(iren)
plane_widget.SetRepresentation(rep)
plane_widget.AddObserver(
    vtkCommand.InteractionEvent,
    my_callback
)

renderer.GetActiveCamera().Azimuth(-60)
renderer.GetActiveCamera().Elevation(30)
renderer.ResetCamera()
renderer.GetActiveCamera().Zoom(0.75)

# Render and interact
iren.Initialize()
ren_win.Render()
plane_widget.On()

# Begin mouse interaction
iren.Start()
