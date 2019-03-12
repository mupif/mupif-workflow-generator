import mupif
import models
import models


class MyProblemClassWorkflow(mupif.Workflow.Workflow):
    
    def __init__(self):
        mupif.Workflow.Workflow.__init__(self)
        self.metadata.update({'Name': 'MyProblemClassWorkflow'})
        self.metadata.update({'Inputs': [{'Name': 'top_temperature', 'Type': 'Property', 'optional': False, 'description': '', 'Type_ID': 'mupif.FieldID.FID_Temperature', 'Object_ID': 'top_temperature'}]})
        self.metadata.update({'Outputs': [{'Name': 'temperature', 'Type': 'Field', 'optional': True, 'description': '', 'Type_ID': 'mupif.FieldID.FID_Temperature', 'Object_ID': 'temperature'}, {'Name': 'displacement', 'Type': 'Field', 'optional': True, 'description': '', 'Type_ID': 'mupif.FieldID.FID_Displacement', 'Object_ID': 'displacement'}]})
    
        # initialization code of external input
        self.external_input_1 = None
        # It should be defined from outside using set() method.
        
        # __init__ code of constant_property_1 ()
        self.constant_property_1 = mupif.Property.ConstantProperty((0.0,), mupif.PropertyID.PID_Temperature, mupif.ValueType.Scalar, mupif.Physics.PhysicalQuantities._unit_table['degC'], None, 0)
        
        # __init__ code of constant_property_2 ()
        self.constant_property_2 = mupif.Property.ConstantProperty((0.0,), mupif.PropertyID.PID_Temperature, mupif.ValueType.Scalar, mupif.Physics.PhysicalQuantities._unit_table['degC'], None, 0)
        
        # __init__ code of model_1 (thermal_nonstat)
        self.model_1 = models.thermal_nonstat()
        
        # __init__ code of model_2 (mechanical)
        self.model_2 = models.mechanical()
    
    def initialize(self, file='', workdir='', executionID=None, metaData={}, **kwargs):
        mupif.Workflow.Workflow.initialize(self, file, workdir, executionID, metaData, **kwargs)
        
        # __init__ code of model_1 (thermal_nonstat)
        self.model_1.initialize(file='inputT13.in', workdir='.')
        
        # __init__ code of model_2 (mechanical)
        self.model_2.initialize(file='inputM13.in', workdir='.')
    
    def getCriticalTimeStep(self):
        return min([self.model_1.getCriticalTimeStep(), self.model_2.getCriticalTimeStep()])
    
    # set method for all external inputs
    def set(self, obj, objectID=0):
            
        # in case of Property
        if isinstance(obj, mupif.Property.Property):
            pass
            if objectID == 'top_temperature':
                self.external_input_1 = obj
            
        # in case of Field
        if isinstance(obj, mupif.Field.Field):
            pass
            
        # in case of Function
        if isinstance(obj, mupif.Function.Function):
            pass
    
    # get method for all external outputs
    def get(self, objectType, time=None, objectID=0):
            
        # in case of Property
        if isinstance(objectType, mupif.PropertyID):
            pass
            
        # in case of Field
        if isinstance(objectType, mupif.FieldID):
            pass
            if objectID == 'temperature':
                return self.model_1.get(mupif.FieldID.FID_Temperature, time, 0)
            if objectID == 'displacement':
                return self.model_2.get(mupif.FieldID.FID_Displacement, time, 0)
            
        # in case of Function
        if isinstance(objectType, mupif.FunctionID):
            pass
        
        return None
    
    def terminate(self):
        self.model_1.terminate()
        self.model_2.terminate()
    
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        
        # execution code of model_1 (thermal_nonstat)
        self.model_1.set(self.external_input_1, 3)
        self.model_1.set(self.constant_property_1, 11)
        self.model_1.set(self.constant_property_2, 14)
        self.model_1.solveStep(tstep)
        
        # execution code of model_2 (mechanical)
        self.model_2.set(self.model_1.get(mupif.FieldID.FID_Temperature, tstep.getTime(), 0), 0)
        self.model_2.solveStep(tstep)

