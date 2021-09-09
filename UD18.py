#!/usr/bin/python3
#

import threading
import serial
import os
import copy
import sys
import glob
import datetime
import time
import argparse
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, Pango, Gio, GObject
from gi.repository.GdkPixbuf import Pixbuf, InterpType
import cairo
from io import StringIO
from decimal import *
import binascii

class MyGui(Gtk.Application):
	def __init__(self):
		Gtk.Application.__init__(self)
		if len(sys.argv) != 2:
			print("")
			print("USAGE:")
			print("	" + sys.argv[0] + " SERIAL_PORT (ex. rfcomm0)")
			print("")
			exit(1)
		self.port = sys.argv[1]
		self.baud = 9600
		self.serial = serial.Serial(self.port, self.baud, timeout=10)
		thread = threading.Thread(target=self.read_from_port)
		thread.start()

	def read_from_port(self):
		self.running = True
		time.sleep(0.2)
		reading = self.serial.read_until(chr(255), 36)
		print("read:", reading.hex())
		while self.running == True:
			reading = self.serial.read(4)
			print("read:", reading.hex())
			if reading[0] == 255 and reading[1] == 85 and reading[2] == 1 and reading[3] == 3:
				t = self.serial.read(3)
				voltage = Decimal(t[0]*65536 + t[1]*256 + t[2]) / Decimal(100);

				t = self.serial.read(3)
				ampere = Decimal(t[0]*65536 + t[1]*256 + t[2]) / Decimal(100);

				t = self.serial.read(3)
				capacity = Decimal(t[0]*65536 + t[1]*256 + t[2])

				t = self.serial.read(4)
				whs = Decimal(t[0]*16777216 + t[1]*65536 + t[2]*256 + t[3])

				t = self.serial.read(2)
				dminus = Decimal(t[0]*256 + t[1]) / Decimal(100);

				t = self.serial.read(2)
				dplus = Decimal(t[0]*256 + t[1]) / Decimal(100);

				t = self.serial.read(3)

				t = self.serial.read(3)
				hours = t[0]
				minutes = t[1]
				secs = t[2]
				distime = str(hours) + ":" + str(minutes) + ":" + str(secs)

				t = self.serial.read(9)

				timestamp = time.time()

				print("V:", voltage, "A:", ampere, "mAh:", capacity, "Wh:", whs, "D-:", dminus, "D+:", dplus, "time:", distime)

				self.timedata.append([timestamp, float(voltage), float(ampere), float(capacity)])
				self.samples.set_markup("<span size='x-large'>Samples: " + str(len(self.timedata)) + "</span>")
				self.voltage.set_markup("<span foreground='blue' size='x-large'>Voltage: " + str(voltage) + "</span>")
				self.ampere.set_markup("<span foreground='red' size='x-large'>Ampere: " + str(ampere) + "</span>")
				self.capacity.set_markup("<span foreground='#ab00ab' size='x-large'>Capacity: " + str(capacity) + "</span>")
				self.time.set_markup("<span size='x-large'>Time: " + distime + "</span>")
				self.timeline.queue_draw()

			else:
				print("unknown reading:", reading.hex())


	def do_activate(self):
		self.timedata = []
		self.window = Gtk.ApplicationWindow(application=self)
		self.window.connect("destroy", self.quit_callback)
		titlebar = self.create_titlebar()
		self.window.set_titlebar(titlebar)

		mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.window.add(mainbox)

		mainbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		mainbox.pack_start(mainbox2, True, True, 0)

		timevaluebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		mainbox2.pack_start(timevaluebox, True, True, 0)

		timeline = self.create_timeline()
		timevaluebox.pack_start(timeline, True, True, 0)

		valuebox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		timevaluebox.add(valuebox)
		self.samples = Gtk.Label(label="--")
		valuebox.pack_start(self.samples, True, True, 0)
		self.voltage = Gtk.Label(label="--")
		valuebox.pack_start(self.voltage, True, True, 0)
		self.ampere = Gtk.Label(label="--")
		valuebox.pack_start(self.ampere, True, True, 0)
		self.capacity = Gtk.Label(label="--")
		valuebox.pack_start(self.capacity, True, True, 0)
		self.time = Gtk.Label(label="--")
		valuebox.pack_start(self.time, True, True, 0)
		self.stat = Gtk.Label(label="--")
		valuebox.pack_start(self.stat, True, True, 0)

		buttonbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		mainbox.add(buttonbox)
		btn_resetmAh = Gtk.Button.new_with_label("Reset mAh")
		btn_resetmAh.connect("clicked", self.btn_resetmAh)
		buttonbox.pack_start(btn_resetmAh, True, True, 0)
		btn_resetWh = Gtk.Button.new_with_label("Reset Wh")
		btn_resetWh.connect("clicked", self.btn_resetWh)
		buttonbox.pack_start(btn_resetWh, True, True, 0)
		btn_resettime = Gtk.Button.new_with_label("Reset Time")
		btn_resettime.connect("clicked", self.btn_resettime)
		buttonbox.pack_start(btn_resettime, True, True, 0)
		btn_resetall = Gtk.Button.new_with_label("Reset All")
		btn_resetall.connect("clicked", self.btn_resetall)
		buttonbox.pack_start(btn_resetall, True, True, 0)

		self.window.show_all()

	def btn_resetWh(self, button):
		self.stat.set_text("Reset Watt-hour")
		self.serial.write(bytearray.fromhex("ff551103010000000051"))

	def btn_resetmAh(self, button):
		self.stat.set_text("Reset mAh")
		self.serial.write(bytearray.fromhex("ff551103020000000052"))

	def btn_resettime(self, button):
		self.stat.set_text("Reset Time")
		self.serial.write(bytearray.fromhex("ff551103030000000053"))

	def btn_resetall(self, button):
		self.stat.set_text("Reset All")
		self.serial.write(bytearray.fromhex("ff55110305000000005d"))

	def quit_callback(self, action):
		self.running = False
		self.quit()

	def create_titlebar(self):
		hb = Gtk.HeaderBar()
		hb.set_show_close_button(True)
		hb.props.title = "Atorch UD18 (Load Tester)"
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		Gtk.StyleContext.add_class(box.get_style_context(), "linked")
		hb.pack_start(box)
		## Menuheader
		menubutton = Gtk.MenuButton.new()
		menumodel = Gio.Menu()
		menumodel.append("Export", "app.export")
		export_as = Gio.SimpleAction.new("export", None)
		export_as.connect("activate", self.export_as)
		self.add_action(export_as)
		menubutton.set_menu_model(menumodel)
		box.add(menubutton)
		return hb


	def timeline_draw_event(self, da, cairo_ctx):
		self.cw = self.timeline.get_allocation().width
		self.ch = self.timeline.get_allocation().height
		gx = 150
		gw = self.cw - gx - 50
		gh = self.ch - 10 - 10
		dl = len(self.timedata)
		if dl == 0:
			return

		cairo_ctx.set_source_rgb(0.0, 0.0, 0.0)
		cairo_ctx.rectangle(gx - 1, 10 - 1, gw + 1, gh + 1)
		cairo_ctx.fill()

		# Grig
		cairo_ctx.set_source_rgb(0.5, 0.5, 0.5)
		cairo_ctx.set_line_width(0.5)
		for n in range(0, 50, 5):
			y = self.ch - 10 - int(n * gh / 50)
			cairo_ctx.new_path()
			cairo_ctx.move_to(gx, y)
			cairo_ctx.line_to(gx + gw, y)
			cairo_ctx.stroke()

		# Voltage
		cairo_ctx.set_line_width(1.0)
		cairo_ctx.set_source_rgb(0.0, 0.0, 1.0)
		for n in range(0, 20 + 5, 5):
			y = self.ch - 10 - int(n * gh / 20)
			cairo_ctx.move_to(gx + gw + 10, y + 3)
			cairo_ctx.show_text(str(n) + "V")
			cairo_ctx.new_path()
			cairo_ctx.move_to(gx + gw, y)
			cairo_ctx.line_to(gx + gw + 5, y)
			cairo_ctx.stroke()
		cairo_ctx.new_path()
		tn = 1;
		for data in self.timedata:
			x = gx + tn * gw / dl
			y = self.ch - 10 - int(data[1] * gh / 20.0)
			if  tn == 1:
				cairo_ctx.move_to(gx, y)
			cairo_ctx.line_to(x, y)
			tn = tn + 1
		cairo_ctx.stroke()

		# Ampere
		cairo_ctx.set_source_rgb(1.0, 0.0, 0.0)
		for n in range(0, 50 + 10, 10):
			y = self.ch - 10 - int(n * gh / 50)
			cairo_ctx.move_to(10, y + 3)
			cairo_ctx.show_text(str(n / 10.0) + "A")
			cairo_ctx.new_path()
			cairo_ctx.move_to(gx - 5, y)
			cairo_ctx.line_to(gx, y)
			cairo_ctx.stroke()
		cairo_ctx.new_path()
		tn = 1;
		for data in self.timedata:
			x = gx + tn * gw / dl
			y = self.ch - 10 - int(data[2] * gh / 5.0)
			if  tn == 1:
				cairo_ctx.move_to(gx, y)
			cairo_ctx.line_to(x, y)
			tn = tn + 1
		cairo_ctx.stroke()


		# Capacity
		capacity_max = (int(self.timedata[-1][3]) + 1) * 10
		if capacity_max < 5:
			capacity_max = 5
		steps = int(capacity_max / 4)
		scale = 10
		cairo_ctx.set_source_rgb(1.0, 0.0, 1.0)
		for n in range(0, int(capacity_max * scale) + steps, steps):
			y = self.ch - 10 - int(n * gh / capacity_max)
			cairo_ctx.move_to(50, y + 3)
			cairo_ctx.show_text(str(n / scale) + "mAh")
			cairo_ctx.new_path()
			cairo_ctx.move_to(gx - 5, y)
			cairo_ctx.line_to(gx, y)
			cairo_ctx.stroke()
		cairo_ctx.new_path()
		tn = 1;
		for data in self.timedata:
			x = gx + tn * gw / dl
			y = self.ch - 10 - int(data[3] * gh / capacity_max * scale)
			if  tn == 1:
				cairo_ctx.move_to(gx, y)
			cairo_ctx.line_to(x, y)
			tn = tn + 1
		cairo_ctx.stroke()


		# Time
#		time_max = int(self.timedata[-1][4].split(":")[0]) * 60 + int(self.timedata[-1][4].split(":")[1]) + 2
#		if time_max < 10:
#			time_max = 10
#		steps = int(time_max / 4)
#		scale = 1
#		cairo_ctx.set_source_rgb(1.0, 1.0, 0.0)
#		for n in range(0, time_max + steps, steps):
#			y = self.ch - 10 - int(n * gh / time_max)
#			cairo_ctx.move_to(100, y + 3)
#			cairo_ctx.show_text(str(int(n / scale)) + "min")
#			cairo_ctx.new_path()
#			cairo_ctx.move_to(gx - 5, y)
#			cairo_ctx.line_to(gx, y)
#			cairo_ctx.stroke()
#		cairo_ctx.new_path()
#		tn = 1;
#		for data in self.timedata:
#			x = gx + tn * gw / dl
#			time_m = int(data[4].split(":")[0]) * 60 + int(data[4].split(":")[1])
#			y = self.ch - 10 - int(time_m * gh / time_max * scale)
#			if  tn == 1:
#				cairo_ctx.move_to(gx, y)
#			cairo_ctx.line_to(x, y)
#			tn = tn + 1
#		cairo_ctx.stroke()


		cairo_ctx.set_source_rgb(0.0, 0.0, 0.0)
		cairo_ctx.rectangle(gx - 1, 10 - 1, gw + 1, gh + 1)
		cairo_ctx.stroke()

	def timeline_configure_event(self, da, event):
		allocation = da.get_allocation()
		self.surface = da.get_window().create_similar_surface(cairo.CONTENT_COLOR, allocation.width, allocation.height)
		cairo_ctx = cairo.Context(self.surface)
		cairo_ctx.set_source_rgb(1, 1, 1)
		cairo_ctx.paint()
		return True

	def create_timeline(self):
		self.timeline = Gtk.DrawingArea()
		self.timeline.set_size_request(1000, 300)
		self.timeline.add_events(Gdk.EventMask.EXPOSURE_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.SCROLL_MASK)
		self.timeline.connect('draw', self.timeline_draw_event)
		self.timeline.connect('configure-event', self.timeline_configure_event)
#		self.timeline.connect('button-press-event', self.timeline_clicked)
		return self.timeline

	def export_as(self, action, parameter):
		dialog = Gtk.FileChooserDialog("Please choose a file", self.window, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
		filter_xmeml = Gtk.FileFilter()
		filter_xmeml.set_name("CSV-Data")
		filter_xmeml.add_pattern("*.csv")
		dialog.add_filter(filter_xmeml)
		filter_any = Gtk.FileFilter()
		filter_any.set_name("Any files")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			print("CSV-Data save to " + dialog.get_filename())
			filename = dialog.get_filename()
			if not "." in filename:
				filename += ".csv"
			file = open(filename, "w")
			for data in self.timedata:
				line = ""
				for part in data:
					line += str(part) + ";"
				line = line.strip(";")
				file.write(line + "\r\n")
			file.close()
		dialog.destroy()



app = MyGui()

exit_status = app.run()
sys.exit(exit_status)

