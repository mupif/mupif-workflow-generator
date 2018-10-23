
class FireDynamicSimulator:
    def __init__(self):
        pass

    def getMetaData(self):
        metadata = {'name': 'FireDynamicsSimulator', 'type': 'CFD', 'inputs': [], 'outputs': [
            {'name': 'ASTField', 'type': 'field', 'optional': True,
             'description': 'Field of adiabatic surface temperature'}]}
        return metadata


class HeatSolver:
    def __init__(self):
        pass

    def getMetaData(self):
        metadata = {'name': 'HeatSolver', 'type': 'Thermal analysis',
                    'inputs': [{'name': 'ASTField', 'type': 'field', 'optional': False,
                                'description': 'Field of adiabatic surface temperature'}],
                    'outputs': [{'name': 'TemperatureField', 'type': 'field', 'optional': True,
                                 'description': 'Field of resulting temperature'}]}
        return metadata


class MechanicalSolver:
    def __init__(self):
        pass

    def getMetaData(self):
        metadata = {'name': 'MechanicalSolver', 'type': 'Mechanical analysis',
                    'inputs': [{'name': 'TemperatureField', 'type': 'field', 'optional': False,
                                'description': 'Field of temperature in the structural domain'}],
                    'outputs': [{'name': 'DisplacementField', 'type': 'field', 'optional': True,
                                 'description': 'Field of resulting displacements'}]}
        return metadata
