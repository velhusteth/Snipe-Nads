import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess
import logging

class MonadBotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MonadSniper"
    _svc_display_name_ = "Monad Sniper Bot"
    _svc_description_ = "Telegram bot for trading on Monad blockchain"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

        # Set up logging
        logging.basicConfig(
            filename='C:\\MonadBot\\logs\\service.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('MonadBotService')

    def SvcStop(self):
        """Stop the service"""
        self.logger.info('Stopping service...')
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.process:
            self.process.terminate()

    def SvcDoRun(self):
        """Run the service"""
        try:
            self.logger.info('Starting service...')
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )

            # Path to your virtual environment Python and bot script
            venv_python = r"C:\MonadBot\venv\Scripts\python.exe"
            bot_script = r"C:\MonadBot\bot.py"

            # Start the bot process
            self.process = subprocess.Popen(
                [venv_python, bot_script],
                cwd=r"C:\MonadBot",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for the stop event
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

        except Exception as e:
            self.logger.error(f'Service error: {str(e)}')
            servicemanager.LogErrorMsg(str(e))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MonadBotService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MonadBotService) 