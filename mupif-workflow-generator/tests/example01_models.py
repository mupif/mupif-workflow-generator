from mupif import Application as mupifApplication


class FireDynamicsSimulator(mupifApplication.Application):
    def __init__(self):
        mupifApplication.Application.__init__(self)
        self.metadata.update({'name': 'FireDynamicsSimulator', 'type': 'CFD', 'inputs': [], 'outputs': [
            {'name': 'ASTField', 'type': 'field', 'optional': True,
             'description': 'Field of adiabatic surface temperature'}]})


class HeatSolver(mupifApplication.Application):
    def __init__(self):
        mupifApplication.Application.__init__(self)
        self.metadata.update({'name': 'HeatSolver', 'type': 'Thermal analysis',
                    'inputs': [{'name': 'ASTField', 'type': 'field', 'optional': False,
                                'description': 'Field of adiabatic surface temperature'}],
                    'outputs': [{'name': 'TemperatureField', 'type': 'field', 'optional': True,
                                 'description': 'Field of resulting temperature'}]})


class MechanicalSolver(mupifApplication.Application):
    def __init__(self):
        mupifApplication.Application.__init__(self)
        self.metadata.update({'name': 'MechanicalSolver', 'type': 'Mechanical analysis',
                    'inputs': [{'name': 'TemperatureField', 'type': 'field', 'optional': False,
                                'description': 'Field of temperature in the structural domain'}],
                    'outputs': [{'name': 'DisplacementField', 'type': 'field', 'optional': True,
                                 'description': 'Field of resulting displacements'}]})


#     self.metadata = {}
#
# def getMetadata(self, key):
#     """
#     Returns metadata associated to given key
#     :param key: unique metadataID
#     :return: metadata associated to key, throws TypeError if key does not exist
#     :raises: TypeError
#     """
#     return self.metadata[key];
#
# def hasMetadata(self, key):
#     """
#     Returns true if key defined
#     :param key: unique metadataID
#     :return: true if key defined, false otherwise
#     :rtype: bool
#     """
#     return self.metadata.has_key(key)
