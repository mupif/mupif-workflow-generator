import mupif


class FireDynamicsSimulator(mupif.Application.Application):
    def __init__(self):
        mupif.Application.Application.__init__(self)
        self.metadata.update({'name': 'FireDynamicsSimulator', 'type': 'CFD', 'inputs': [], 'outputs': [
            {'name': 'ASTField', 'type': 'Field', 'optional': True,
             'description': 'Field of adiabatic surface temperature',
             'obj_type': 'mupif.FieldID.FID_Temperature', 'obj_id': 'temperature'}]})

    def getCriticalTimeStep(self):
        return mupif.Physics.PhysicalQuantities.PhysicalQuantity(1.0, 's')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        print("Imaginary solveStep of CFD")


class HeatSolver(mupif.Application.Application):
    def __init__(self):
        mupif.Application.Application.__init__(self)
        self.metadata.update({'name': 'HeatSolver', 'type': 'Thermal analysis',
                    'inputs': [{'name': 'ASTField', 'type': 'Field', 'optional': False,
                                'description': 'Field of adiabatic surface temperature',
                                'obj_type': 'mupif.FieldID.FID_Temperature', 'obj_id': 'temperature'}],
                    'outputs': [{'name': 'TemperatureField', 'type': 'Field', 'optional': True,
                                 'description': 'Field of resulting temperature',
                                 'obj_type': 'mupif.FieldID.FID_Temperature', 'obj_id': 'temperature'}]})

    def getCriticalTimeStep(self):
        return mupif.Physics.PhysicalQuantities.PhysicalQuantity(1.0, 's')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        print("Imaginary solveStep of thermal task")


class MechanicalSolver(mupif.Application.Application):
    def __init__(self):
        mupif.Application.Application.__init__(self)
        self.metadata.update({'name': 'MechanicalSolver', 'type': 'Mechanical analysis',
                    'inputs': [{'name': 'TemperatureField', 'type': 'Field', 'optional': False,
                                'description': 'Field of temperature in the structural domain',
                                 'obj_type': 'mupif.FieldID.FID_Temperature', 'obj_id': 'temperature'}],
                    'outputs': [{'name': 'DisplacementField', 'type': 'Field', 'optional': True,
                                 'description': 'Field of resulting displacements',
                                 'obj_type': 'mupif.FieldID.FID_Displacement', 'obj_id': 'displacement'}]})

    def getCriticalTimeStep(self):
        return mupif.Physics.PhysicalQuantities.PhysicalQuantity(1.0, 's')

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        print("Imaginary solveStep of mechanical task")

