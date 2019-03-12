import mupif
import sys
sys.path.append('../../..')
import workfloweditor
import workflowgenerator

if __name__ == '__main__':

    workflow = workflowgenerator.BlockWorkflow.BlockWorkflow()

    #

    application = workfloweditor.Application.Application(workflow)
    application.window.setGeometry(400, 200, 400, 800)
    application.generateAll()
    application.run()
