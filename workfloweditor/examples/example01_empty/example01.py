import sys
sys.path.append('../../..')
import workfloweditor

if __name__ == '__main__':

    application = workfloweditor.Application.Application()
    application.window.setGeometry(400, 200, 400, 500)
    application.generateAll()
    application.run()
