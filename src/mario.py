import asyncio
import time
import wx
from wxasync import WxAsyncApp, StartCoroutine
from pynput.keyboard import Key, Controller , KeyCode
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.uuids import uuid16_dict, uuid128_dict
import math


# Timing
BUTTON_TIME_DEFAULT = 0.1
BUTTON_TIME_JUMP = 0.5

keys=["up","down","right","left","space","shift","control","a","w","s","d","n","m"]
keys_=[Key.up,Key.down,Key.right,Key.left,Key.space,Key.shift,Key.ctrl,'a','w','s','d','n','m']

## Default Key assignments
KEY_JUMP = keys.index("space")
KEY_LEAN_FORWARD = keys.index("right")
KEY_LEAN_BACKWARD = keys.index("left")
KEY_RED_TILE = keys.index("shift")
KEY_GREEN_TILE = keys.index("down")
KEY_START_TILE = keys.index("w")
KEY_GOAL_TILE = keys.index("s")


# BLE stuff
LEGO_CHARACTERISTIC_UUID = "00001624-1212-efde-1623-785feabcd123"

SUBSCRIBE_IMU_COMMAND = bytearray([0x0A, 0x00, 0x41, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0x01])
SUBSCRIBE_RGB_COMMAND = bytearray([0x0A, 0x00, 0x41, 0x01, 0x00, 0x05, 0x00, 0x00, 0x00, 0x01])

# GUI class
class MarioFrame(wx.Frame):

    def __init__(self, parent=None, id=-1, title="Lego Super Mario Controller"):
        wx.Frame.__init__(self, parent, id, title, size=(450, 400))
        self.initGUI()
        self.controller = MarioController(self)
        StartCoroutine(self.controller.run(), self)

    def initGUI(self):

        panel = wx.Panel(self)

        font = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.DEFAULT)

        self.status_field = wx.StaticText(self, label="", pos=(10, 5))
        self.status_field.SetFont(font)
        
        self.accel_field_title = wx.StaticText(self, label="Accelerometer and Camera Data:", pos=(10,40), size=wx.Size(200, wx.DefaultCoord))
        self.accel_field_title.SetFont(font)
        
        self.accel_field = wx.StaticText(self, label="X: 0 | Y: 0 | Z: 0", pos=(20,70), size=wx.Size(100, wx.DefaultCoord))
        self.accel_field.SetFont(font)
        
        self.accel_vector = wx.StaticText(self, label="R: 0.0 | T: 0.0 | P: 0.0", pos=(200,70), size=wx.Size(100, wx.DefaultCoord))
        self.accel_vector.SetFont(font)
        
        self.cam_field = wx.StaticText(self, label="Camera: No tile", pos=(20,100), size=wx.Size(100, wx.DefaultCoord))
        self.cam_field.SetFont(font)
        
        self.accel_field_title = wx.StaticText(self, label="Key Settings:", pos=(10,135), size=wx.Size(100, wx.DefaultCoord))
        self.accel_field_title.SetFont(font)
        
        self.key_switch_label = wx.StaticText(self, label="Send keys: ", pos=(300,135), size=wx.Size(100, wx.DefaultCoord))
        self.key_switch_label.SetFont(font)
        self.key_switch = wx.CheckBox(self,pos=(400,135) )
        
        self.keyForward_label = wx.StaticText(self, label="Forward Key:", pos=(10,170), size=wx.Size(100, wx.DefaultCoord))
        self.keyForward_label.SetFont(font)
        self.keyForwardCombo = wx.ComboBox(self, pos=(130,168), choices = keys, style=wx.CB_READONLY)
        self.keyForwardCombo.SetFont(font)
        
        self.keyBackard_label = wx.StaticText(self, label="Backard Key:", pos=(230,170), size=wx.Size(100, wx.DefaultCoord))
        self.keyBackard_label.SetFont(font)
        self.keyBackwardCombo = wx.ComboBox(self, style=wx.CB_READONLY, pos=(350,168) ,choices = keys)
        self.keyBackwardCombo.SetFont(font)
        
        self.keyJump_label = wx.StaticText(self, label="Jump Key:", pos=(10,210), size=wx.Size(100, wx.DefaultCoord))
        self.keyJump_label.SetFont(font)
        self.keyJumpCombo = wx.ComboBox(self, pos=(130,208), choices = keys, style=wx.CB_READONLY)
        self.keyJumpCombo.SetFont(font)
        
        self.keyRedTile_label = wx.StaticText(self, label="Red Tile Key:", pos=(230,210), size=wx.Size(100, wx.DefaultCoord))
        self.keyRedTile_label.SetFont(font)
        self.keyRedTileCombo = wx.ComboBox(self, style=wx.CB_READONLY, pos=(350,208) ,choices = keys)
        self.keyRedTileCombo.SetFont(font)
        
        self.keyGreenTile_label = wx.StaticText(self, label="Green Tile Key:", pos=(10,250), size=wx.Size(100, wx.DefaultCoord))
        self.keyGreenTile_label.SetFont(font)
        self.keyGreenTileCombo = wx.ComboBox(self, pos=(130,248), choices = keys, style=wx.CB_READONLY)
        self.keyGreenTileCombo.SetFont(font)
        
        self.keyStartTile_label = wx.StaticText(self, label="Start Tile Key:", pos=(230,250), size=wx.Size(100, wx.DefaultCoord))
        self.keyStartTile_label.SetFont(font)
        self.keyStartTileCombo = wx.ComboBox(self, style=wx.CB_READONLY, pos=(350,248) ,choices = keys)
        self.keyStartTileCombo.SetFont(font)
        
        self.keyGoalTile_label = wx.StaticText(self, label="Goal Tile Key:", pos=(10,290), size=wx.Size(100, wx.DefaultCoord))
        self.keyGoalTile_label.SetFont(font)
        self.keyGoalTileCombo = wx.ComboBox(self, pos=(130,288), choices = keys, style=wx.CB_READONLY)
        self.keyGoalTileCombo.SetFont(font)
        
        # Default Key Value
        self.keyJumpCombo.SetSelection(KEY_JUMP)
        self.keyForwardCombo.SetSelection(KEY_LEAN_FORWARD)
        self.keyBackwardCombo.SetSelection(KEY_LEAN_BACKWARD)
        self.keyRedTileCombo.SetSelection(KEY_RED_TILE)
        self.keyGreenTileCombo.SetSelection(KEY_GREEN_TILE)
        self.keyStartTileCombo.SetSelection(KEY_START_TILE)
        self.keyGoalTileCombo.SetSelection(KEY_GOAL_TILE)

# Class for the controller
class MarioController:

    def __init__(self, gui):
        self.gui = gui
        self.keyboard = Controller()
        self.current_tile = 0
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.is_connected = False

    def signed(char):
        return char - 256 if char > 127 else char

    async def process_keys(self):
        
        if self.is_connected and self.gui.key_switch.GetValue():
        
            KEY_JUMP = keys_[self.gui.keyJumpCombo.GetSelection()]
            KEY_LEAN_FORWARD = keys_[self.gui.keyForwardCombo.GetSelection()]
            KEY_LEAN_BACKWARD = keys_[self.gui.keyBackwardCombo.GetSelection()]
            KEY_RED_TILE = keys_[self.gui.keyRedTileCombo.GetSelection()]
            KEY_GREEN_TILE = keys_[self.gui.keyGreenTileCombo.GetSelection()]
            KEY_START_TILE = keys_[self.gui.keyStartTileCombo.GetSelection()]
            KEY_GOAL_TILE = keys_[self.gui.keyGoalTileCombo.GetSelection()]
            
            if self.current_tile == 1:
                self.keyboard.press(KEY_RED_TILE)
                await asyncio.sleep(BUTTON_TIME_DEFAULT)
                self.keyboard.release(KEY_RED_TILE)
                self.current_tile = 0
            elif self.current_tile == 2:
                self.keyboard.press(KEY_GREEN_TILE)
                await asyncio.sleep(BUTTON_TIME_DEFAULT)
                self.keyboard.release(KEY_GREEN_TILE)
                self.current_tile = 0
            elif self.current_tile == 3:
                self.keyboard.press(KEY_START_TILE)
                await asyncio.sleep(BUTTON_TIME_DEFAULT)
                self.keyboard.release(KEY_START_TILE)
                self.current_tile = 0
            elif self.current_tile == 4:
                self.keyboard.press(KEY_GOAL_TILE)
                await asyncio.sleep(BUTTON_TIME_DEFAULT)
                self.keyboard.release(KEY_GOAL_TILE)
                self.current_tile = 0
            if self.phi <= 1:
                self.keyboard.press(KEY_LEAN_BACKWARD)
            elif self.phi >= 2:
                self.keyboard.press(KEY_LEAN_FORWARD)
            else:
                self.keyboard.release(KEY_LEAN_BACKWARD)
                self.keyboard.release(KEY_LEAN_FORWARD)
            if self.tetha >= 0.7 or self.tetha <= -0.7: 
                self.keyboard.press(KEY_JUMP)
                await asyncio.sleep(BUTTON_TIME_JUMP)
                self.keyboard.release(KEY_JUMP)
        await asyncio.sleep(0.05)


    def notification_handler(self, sender, data):
        # Camera sensor data
        if data[0] == 8:

            # RGB code
            if data[5] == 0x0:
                if data[4] == 0xb8:
                    self.gui.cam_field.SetLabel("Camera: Start tile")
                    self.current_tile = 3
                if data[4] == 0xb7:
                    self.gui.cam_field.SetLabel("Camera: Goal tile")
                    self.current_tile = 4
                print("Barcode: " + " ".join(hex(n) for n in data))

            # Red tile
            elif data[6] == 0x15:
                self.gui.cam_field.SetLabel("Camera: Red tile")
                self.current_tile = 1
            # Green tile
            elif data[6] == 0x25:
                self.gui.cam_field.SetLabel("Camera: Green tile")
                self.current_tile = 2
            # No tile
            elif data[6] == 0x1a:
                self.gui.cam_field.SetLabel("Camera: No tile")
                self.current_tile = 0


        # Accelerometer data
        elif data[0] == 7:
            self.current_x = int((self.current_x*0.5) + (MarioController.signed(data[4])*0.5))
            self.current_y = int((self.current_y*0.5) + (MarioController.signed(data[5])*0.5))
            self.current_z = int((self.current_z*0.5) + (MarioController.signed(data[6])*0.5))
            # Accelerometer Vector
            try:
                self.r = math.sqrt(pow(self.current_x,2) + pow(self.current_y,2) + pow(self.current_z,2))
                self.tetha = math.atan(self.current_x/self.current_y)
                self.phi = math.acos(self.current_z / self.r)
            except:
                self.r = 0
                self.tetha = 0
                self.phi = 0
            
            #print("r=%f , tetha=%f , phi=%f" %(self.r,self.tetha,self.phi))
            self.gui.accel_field.SetLabel("X: %i | Y: %i | Z: %i" % (self.current_x, self.current_y, self.current_z))
            self.gui.accel_vector.SetLabel("R: %.2f | T: %.2f | P: %.2f" %(self.r, self.tetha, self.phi))
            


    async def run(self):
        print("Run")
        service_uuids = []
        for item in uuid16_dict:
            service_uuids.append("{0:04x}".format(item))
        service_uuids.extend(uuid128_dict.keys())

        self.gui.status_field.SetLabel("Looking for Mario. Switch on and press Bluetooth key.")
        
        while True:
        
            async with BleakScanner(service_uuids=service_uuids) as scanner:
                await asyncio.sleep(0.5)
            devices = await scanner.discover()
            self.is_connected = False
            
            
            self.gui.status_field.SetLabel("Looking for Mario. Switch on and press Bluetooth key.")
            self.gui.accel_field.SetLabel("X: 0 | Y: 0 | Z: 0")
            self.gui.accel_vector.SetLabel("R: 0.0 | T: 0.0 | P: 0.0")
            self.gui.cam_field.SetLabel("Camera: No tile")
            
            for d in scanner.discovered_devices:
                if d.name.lower().startswith("lego mario") or LEGO_CHARACTERISTIC_UUID in d.metadata['uuids']:
                    self.gui.status_field.SetLabel("Found Super Mario!")
                    try:
                        async with BleakClient(d) as client:
                            await client.is_connected()
                            self.gui.status_field.SetLabel("Mario is connected")
                            self.is_connected = True
                            await client.start_notify(LEGO_CHARACTERISTIC_UUID, self.notification_handler)
                            await asyncio.sleep(0.1)
                            await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, SUBSCRIBE_IMU_COMMAND)
                            await asyncio.sleep(0.1)
                            await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, SUBSCRIBE_RGB_COMMAND)
                            while await client.is_connected():
                                await self.process_keys()
                    except:
                        pass


# Run it
if __name__ == "__main__":
    # The application object.
    app = WxAsyncApp()
    # The app frame
    frm = MarioFrame()
    # Drawing it
    frm.Show()

    # Start the main loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.MainLoop())
