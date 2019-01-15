import mupif
from models import thermal_nonstat
from models import mechanical


class MyProblemClassWorkflow(mupif.Workflow.Workflow):
    def __init__(self):
        mupif.Workflow.Workflow.__init__(self)
        self.metadata.update({'name': 'MyProblemClassWorkflow'})
        self.metadata.update({'inputs': [{'name': 'top_temperature', 'type': 'Property', 'optional': False, 'description': '', 'obj_type': 'mupif.FieldID.FID_Temperature', 'obj_id': 'top_temperature'}]})
        self.metadata.update({'outputs': [{'name': 'temperature', 'type': 'Field', 'optional': True, 'description': '', 'obj_type': 'mupif.FieldID.FID_Temperature', 'obj_id': 'temperature'}, {'name': 'displacement', 'type': 'Field', 'optional': True, 'description': '', 'obj_type': 'mupif.FieldID.FID_Displacement', 'obj_id': 'displacement'}]})
    
        # initialization code of external input
        self.external_input_1 = None
        # It should be defined from outside using set() method.
        
        # initialization code of constant_property_1 (ExecutionBlock)
        self.constant_property_1 = mupif.Property.ConstantProperty((0.0,), mupif.propertyID.PropertyID.PID_Temperature, mupif.ValueType.ValueType.Scalar, mupif.Physics.PhysicalQuantities._unit_table['degC'], None, 0)
        
        # initialization code of constant_property_2 (ExecutionBlock)
        self.constant_property_2 = mupif.Property.ConstantProperty((0.0,), mupif.propertyID.PropertyID.PID_Temperature, mupif.ValueType.ValueType.Scalar, mupif.Physics.PhysicalQuantities._unit_table['degC'], None, 0)
        
        # initialization code of model_1 (thermal_nonstat)
        self.model_1 = thermal_nonstat(file='inputT13.in', workdir='.')
        
        # initialization code of model_2 (mechanical)
        self.model_2 = mechanical(file='inputM13.in', workdir='.')
    
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
    
    # set method for all external inputs
    def get(self, objectType, time=None, objectID=0):
            
        # in case of Property
        if isinstance(objectType, mupif.propertyID.PropertyID):
            pass
            
        # in case of Field
        if isinstance(objectType, mupif.fieldID.FieldID):
            pass
            if objectID == 'temperature':
                return self.model_1.get(mupif.FieldID.FID_Temperature, time, 0)
            if objectID == 'displacement':
                return self.model_2.get(mupif.FieldID.FID_Displacement, time, 0)
            
        # in case of Function
        if isinstance(objectType, mupif.functionID.FunctionID):
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

