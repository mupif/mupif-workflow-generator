import mupif
import class_code
import field_to_vtk


class MyProblemExecutionWorkflow(mupif.Workflow.Workflow):
    
    def __init__(self, metaData={}):
        MD = {
            'Inputs': [
            ],
            'Outputs': [
            ],
        }
        mupif.Workflow.Workflow.__init__(self, metaData=MD)
        self.setMetadata('Name', 'MyProblemExecutionWorkflow')
        self.setMetadata('ID', 'MyProblemExecutionWorkflow')
        self.setMetadata('Description', '')
        self.setMetadata('Model_refs_ID', [])
        self.updateMetadata(metaData)
        
        # __init__ code of constant_physical_quantity_1 ()
        self.constant_physical_quantity_1 = mupif.Physics.PhysicalQuantities.PhysicalQuantity(0.0, 's')
        
        # __init__ code of constant_physical_quantity_2 ()
        self.constant_physical_quantity_2 = mupif.Physics.PhysicalQuantities.PhysicalQuantity(10.0, 's')
        
        # __init__ code of constant_physical_quantity_3 ()
        self.constant_physical_quantity_3 = mupif.Physics.PhysicalQuantities.PhysicalQuantity(0.5, 's')
        
        # __init__ code of constant_property_1 ()
        self.constant_property_1 = mupif.Property.ConstantProperty((10.0,), mupif.PropertyID.PID_Temperature, mupif.ValueType.Scalar, 'degC', None, 0)
        
        # __init__ code of model_1 (MyProblemClassWorkflow)
        self.model_1 = class_code.MyProblemClassWorkflow()
        
        # __init__ code of model_2 (field_export_to_VTK)
        self.model_2 = field_to_vtk.field_export_to_VTK()
        
        # __init__ code of model_3 (field_export_to_VTK)
        self.model_3 = field_to_vtk.field_export_to_VTK()
    
    def initialize(self, file='', workdir='', targetTime=mupif.Physics.PhysicalQuantities.PhysicalQuantity(0., 's'), metaData={}, validateMetaData=True, **kwargs):
        
        mupif.Workflow.Workflow.initialize(self, file=file, workdir=workdir, targetTime=targetTime, metaData=metaData, validateMetaData=validateMetaData, **kwargs)
        
        execMD = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        
        # initialization code of model_1 (MyProblemClassWorkflow)
        self.model_1.initialize(metaData=execMD)
        
        # initialization code of model_2 (field_export_to_VTK)
        self.model_2.initialize(metaData=execMD)
        
        # initialization code of model_3 (field_export_to_VTK)
        self.model_3.initialize(metaData=execMD)
    
    def terminate(self):
        self.model_1.terminate()
        self.model_2.terminate()
        self.model_3.terminate()
    
    def solve(self, runInBackground=False):
        
        # execution code of timeloop_1 ()
        timeloop_1_time = self.constant_physical_quantity_1
        timeloop_1_target_time = self.constant_physical_quantity_2
        timeloop_1_compute = True
        timeloop_1_time_step_number = 0
        while timeloop_1_compute:
            timeloop_1_time_step_number += 1
        
            timeloop_1_dt = min([self.constant_physical_quantity_3, self.model_1.getCriticalTimeStep(), self.model_2.getCriticalTimeStep(), self.model_3.getCriticalTimeStep()])
            timeloop_1_time = min(timeloop_1_time+timeloop_1_dt, timeloop_1_target_time)
        
            if timeloop_1_time.inUnitsOf('s').getValue() + 1.e-6 > timeloop_1_target_time.inUnitsOf('s').getValue():
                timeloop_1_compute = False
            
            timeloop_1_time_step = mupif.TimeStep.TimeStep(timeloop_1_time, timeloop_1_dt, timeloop_1_target_time, n=timeloop_1_time_step_number)
            
            # execution code of model_1 (MyProblemClassWorkflow)
            self.model_1.set(self.constant_property_1, 'top_temperature')
            self.model_1.solveStep(timeloop_1_time_step)
            
            # execution code of model_2 (field_export_to_VTK)
            self.model_2.set(self.model_1.get(mupif.FieldID.FID_Temperature, timeloop_1_time_step.getTime(), 'temperature'), 0)
            self.model_2.solveStep(timeloop_1_time_step)
            
            # execution code of model_3 (field_export_to_VTK)
            self.model_3.set(self.model_1.get(mupif.FieldID.FID_Displacement, timeloop_1_time_step.getTime(), 'displacement'), 0)
            self.model_3.solveStep(timeloop_1_time_step)
        
        # terminate all models
        self.terminate()


if __name__ == '__main__':
    problem = MyProblemExecutionWorkflow()
    
    md = {
        'Execution': {
            'ID': 'N/A',
            'Use_case_ID': 'N/A',
            'Task_ID': 'N/A'
        }
    }
    problem.initialize(metaData=md)
    problem.solve()
    problem.terminate()
    
    print('Simulation has finished.')

