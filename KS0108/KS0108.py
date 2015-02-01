#!/usr/bin/env python
from Adafruit_I2C import Adafruit_I2C
from Adafruit_MCP230xx import Adafruit_MCP230XX
import smbus
import time

class LCD128x64(object):
  """docstring for LCD128x64"""
  def __init__(self, address=0x20, busnum=-1, width=128, height=64, lcdOrientation = 0):
    self.mcp = Adafruit_MCP230XX(address = address, num_gpios = 16, busnum = busnum)
    self.lcd_str  = 8
    self.lcd_rs   = 9
    self.lcd_cs1  = 10
    self.lcd_cs2  = 11
    self.lcd_reset= 12
    self.lcd_data = range(8)
    self.initialized = False
    self.height = height
    self.width = width
    self.framebuffer = height * width *[0]
    self.oldframebuffer = height * width *[0]
    self.maxPos = (0, 0) # x,y
    self.lastPos = (0, 0) # x,y
    self.origin = (0, 0) # x,y
    self.lcdOrientation = lcdOrientation
    self.mcp.config(self.lcd_str, self.mcp.OUTPUT)
    self.mcp.config(self.lcd_rs, self.mcp.OUTPUT)
    self.mcp.config(self.lcd_cs1, self.mcp.OUTPUT)
    self.mcp.config(self.lcd_cs2, self.mcp.OUTPUT)
    self.mcp.config(self.lcd_reset, self.mcp.OUTPUT)
    self.mcp.output(self.lcd_reset, 0)
    self.delayMicroseconds(100)
    self.mcp.output(self.lcd_reset, 1)

    self.mcp.output(self.lcd_cs1, 1)
    self.mcp.output(self.lcd_cs2, 1)
    self.mcp.output(self.lcd_str, 0)
    self.mcp.output(self.lcd_rs, 1)
    for i in self.lcd_data:
      self.mcp.config(i, self.mcp.OUTPUT)
    self.setOrientation(lcdOrientation)

    self.sendCommand(0x3F, self.lcd_cs1)
    self.sendCommand(0xC0, self.lcd_cs1)
    self.sendCommand(0x3F, self.lcd_cs2)
    self.sendCommand(0xC0, self.lcd_cs2)
    self.update()

  def clear(self, colour):
    self.framebuffer = height * width *[colour]

  def strobe(self):
    self.mcp.output(self.lcd_str, 1)
    self.delayMicroseconds(1)
    self.mcp.output(self.lcd_str, 0)
    self.delayMicroseconds(5)
  def sendData(self, data, chip):
    """docstring for sendData"""
    self.mcp.output(chip, 0)
    if self.lcd_data == range(8):
      self.mcp.write8(data & 0xff)
    else:
      for i in range(8):
        self.mcp.output(self.lcd_data[i], (data >> i) & 1)
    self.strobe()
    self.mcp.output(chip, 1)

  def sendCommand(self, command, chip):
    self.mcp.output(self.lcd_rs, 0)
    self.sendData(command, chip)
    self.mcp.output(self.lcd_rs, 1)

  def setCol(self, col, chip):
    self.sendCommand(0x40 | (col  & 0x3F), chip)

  def setLine(self, line, chip):
    self.sendCommand(0xB8 | (line & 0x07), chip)

  def update(self):
    """docstring for lcd128x64update"""
    self.updateWithCheck(0)

  def updateWithCheck(self, checkForChange):
    """docstring for lcd128x64updateWithCheck"""
    # left
    for line in range(8):
      for x in range(62, -1, -1):
        byte = 0
        oldByte = 0
        for y in range(8):
          fbLoc = x + (((7 - line) * 8) + (7 - y)) * self.width
          if self.framebuffer[fbLoc] != 0:
            byte |= (1 << y)
          if self.oldframebuffer[fbLoc] != 0:
            oldByte |= (1 << y)
        if (not checkForChange) or (oldByte ^ byte):
          #print("sendByte l : %i" % byte)
          self.setCol(63 - x, self.lcd_cs1)
          self.setLine(line, self.lcd_cs1)
          self.sendData(byte, self.lcd_cs1)
    #right
    for line in range(8):
      for x in range(127, 63, -1):
        byte = 0
        oldByte = 0
        for y in range(8):
          fbLoc = x + (((7 - line) * 8) + (7 - y)) * self.width
          if self.framebuffer[fbLoc] != 0:
            byte |= (1 << y)
          if self.oldframebuffer[fbLoc] != 0:
            oldByte |= (1 << y)
        if (not checkForChange) or (oldByte ^ byte):
          #print("sendByte r: %i" % byte)
          self.setCol(127 - x, self.lcd_cs2)
          self.setLine(line, self.lcd_cs2)
          self.sendData(byte, self.lcd_cs2)
    self.oldframebuffer = self.framebuffer[:]
  def setOrigin(self, x, y):
    """Set the display offset origin"""
    self.origin = (x, y)

  def setOrientation(self, orientation):
    """Set the display orientation:
  *	0: Normal, the display is portrait mode, 0,0 is top left
  *	1: Landscape
  *	2: Portrait, flipped
  *	3: Landscape, flipped
  """
    self.lcdOrientation = orientation & 3
    self.setOrigin(0, 0)
    if (self.lcdOrientation == 0) or (self.lcdOrientation == 2):
      self.maxPos = (self.width, self.height)
    elif (self.lcdOrientation == 1) or (self.lcdOrientation == 3):
      self.maxPos = (self.height, self.width)

  def orientCoordinates(self, x, y):
    """Adjust the coordinates given to the display orientation"""
    x += self.origin[0]
    y += self.origin[1]
    y = self.maxPos[1] - y - 1
    if self.lcdOrientation == 1:
      tmp = self.maxPos[1] - y - 1
      y = x
      x = tmp
    elif self.lcdOrientation == 2:
      x = self.maxPos[0] - x - 1
      y = self.maxPos[1] - y - 1
    elif self.lcdOrientation == 3:
      x = self.maxPos[0] - x - 1
      tmp = y
      y = x
      x = tmp
    return (x, y)
  def getScreenSize(self):
    """Return the max X & Y screen sizes. Needs to be called again, if you
    change screen orientation."""
    return self.maxPos

  def point(self, x, y, colour):
    """Plot a pixel."""
    self.lastPos = (x, y)
    (x, y) = self.orientCoordinates(x, y)
    if (x < 0) or (x >= self.width) or (y < 0) or (y >= self.height):
      return False
    self.framebuffer[x + y * self.width] = colour
    print("painted point at %i, %i: %i" %(x, y, colour))

  def line(self, x0, y0, x1, y1, colour):
    """Classic Bressenham Line code"""
    self.lastPos = (x1, y1)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx -dy

    while True:
      self.point(x0, y0, colour)

      if (x0 == x1) and (y0 == y1):
        break

      e2 = 2 * err

      if e2 > -dy:
        err -= dy
        x0 += sx
      if e2 < dx:
        err += dx
        y0 += sy
  def lineTo(self, x, y, colour):
    """draw line from last position to (x,y)"""
    self.line(*self.lastPos, x1=x, y1=y, colour=colour)


  def delayMicroseconds(self, microseconds):
    seconds = microseconds / float(1000000)  # divide microseconds by 1 million for seconds
    time.sleep(seconds)

if __name__ == '__main__':

  lcd = LCD128x64(address = 0x23, lcdOrientation=2, busnum=0)
  lcd.update()
  lcd.point (4, 5, 255)
  lcd.point (7, 6, 255)
  lcd.point (4, 15, 255)
  lcd.lineTo(78,54, 255)
  lcd.updateWithCheck(0)
  for i in range(127):
    print("x %i" % i)
    lcd.point (i, 25, 0)
    lcd.point (i+1, 25, 255)
    lcd.updateWithCheck(0)
    time.sleep(.2)



