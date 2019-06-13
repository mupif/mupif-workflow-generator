import mupif


class field_export_to_VTK(mupif.Application.Application):
    def __init__(self):
        mupif.Application.Application.__init__(self)
        self.field = None
        self.step_number = 0
        self.filename_base = "VTKField"
        self.metadata.update({'Name': 'field_export_to_VTK',
                              'ID': 'simpleVtkExport',
                              'Version_date': '1.0 1.5.2019',
                              'Inputs': [
                                  {'Name': 'field', 'Type': 'mupif.Field', 'Required': False,
                                   'Type_ID': 'mupif.FieldID.FID_Temperature'}
                              ],
                              'Outputs': []})

    def initialize(self, file='', workdir='', executionID='', metaData={}, validateMetaData=False, **kwargs):
        pass

    def setField(self, field, objectID=0):
        """

        :param mupif.Field.Field field:
        :param objectID:
        :return:
        """
        self.field = field

    def solveStep(self, tstep, stageID=0, runInBackground=False):
        if self.field:
            if not self.step_number:
                if self.field.fieldID == mupif.FieldID.FID_Temperature:
                    self.filename_base = "VTKField_Temperature"
                if self.field.fieldID == mupif.FieldID.FID_Displacement:
                    self.filename_base = "VTKField_Displacement"

            self.step_number += 1
            self.field.field2VTKData().tofile('%s_%d' % (self.filename_base, self.step_number))

    def getCriticalTimeStep(self):
        return mupif.Physics.PhysicalQuantities.PhysicalQuantity(1000.0, 's')

