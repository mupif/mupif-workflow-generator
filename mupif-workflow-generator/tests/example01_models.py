import mupif


class FireDynamicsSimulator(mupif.Application.Application):
    def __init__(self):
        mupif.Application.Application.__init__(self)
        self.metadata.update({'name': 'FireDynamicsSimulator', 'type': 'CFD', 'inputs': [], 'outputs': [
            {'name': 'ASTField', 'type': 'Field', 'optional': True,
             'description': 'Field of adiabatic surface temperature'}]})


class HeatSolver(mupif.Application.Application):
    def __init__(self):
        mupif.Application.Application.__init__(self)
        self.metadata.update({'name': 'HeatSolver', 'type': 'Thermal analysis',
                    'inputs': [{'name': 'ASTField', 'type': 'Field', 'optional': False,
                                'description': 'Field of adiabatic surface temperature'}],
                    'outputs': [{'name': 'TemperatureField', 'type': 'Field', 'optional': True,
                                 'description': 'Field of resulting temperature'}]})


class MechanicalSolver(mupif.Application.Application):
    def __init__(self):
        mupif.Application.Application.__init__(self)
        self.metadata.update({'name': 'MechanicalSolver', 'type': 'Mechanical analysis',
                    'inputs': [{'name': 'TemperatureField', 'type': 'Field', 'optional': False,
                                'description': 'Field of temperature in the structural domain'}],
                    'outputs': [{'name': 'DisplacementField', 'type': 'Field', 'optional': True,
                                 'description': 'Field of resulting displacements'}]})

