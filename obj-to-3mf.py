#!/usr/bin/env python3
# wavefront obj to 3mf/vrml/amf converter by Arho M
import os
import zipfile
from argparse import ArgumentParser

def make_triangle_fan(indices):
	tris=[]
	for i in range(2,len(indices)):
		tris += [(indices[0], indices[i-1], indices[i])]
	return tris

class Mesh:
	def __init__(self):
		self.v=[] # list of vertices in input string format
		self.f=[] # list of polygons
	def reverse_winding(self):
		self.f = [tuple(reversed(f)) for f in self.f]
	def triangles(self):
		for f in self.f:
			if len(f) != 3:
				for t in make_triangle_fan(f):
					yield t
			else:
				yield f
	def read_obj(self, f):
		for line in f.readlines():
			line=line.strip()
			words=line.split()
			if len(words) > 0:
				if line[0]=='v':
					coords=words[1:]
					if len(coords) != 3:
						raise Exception("Non-3D coordinates")
					self.v += [coords]
				if line[0]=='f':
					idx = [int(w.split('/')[0])-1 for w in words[1:]]
					if len(idx) >= 3:
						self.f += [idx]
	def hi(self):
		print("Vertices:", len(self.v))
		print("Facets:", len(self.f))
	def write_vrml(self, path):
		with open(path,"w") as f:
			f.write("""#VRML V2.0 utf8
DEF _Plane Transform {
children [
Shape {
	appearance Appearance {
		material Material {
			diffuseColor 0.47 0.47 0.47
			emissiveColor 0 0 0
			specularColor 1 1 1
			ambientIntensity 1
			transparency 0
			shininess 0.5
		}
	}
	geometry IndexedFaceSet {
		coord Coordinate { point [\n""" +
			',\n'.join("\t\t\t"+" ".join(v) for v in self.v) +
				" ]\n\t\t}\n\t\tcoordIndex [\n" +
			',\n'.join("\t\t\t%d, %d, %d, -1" % f for f in self.triangles()) +
			" ]\n\t}\n}\n]\n}\n")
	def format_3mf_mesh(self):
		s="""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
<resources>
<object id="1" type="model">
<mesh>
<vertices>\n"""
		for x,y,z in self.v:
			s += '<vertex x="{}" y="{}" z="{}" />'.format(x,y,z)
		s += '\n</vertices>\n<triangles>\n'
		for a,b,c in self.triangles():
			s += '<triangle v1="{}" v2="{}" v3="{}" />'.format(a,b,c)
		s += """</triangles>\n
</mesh>
</object>
</resources>
<build><item objectid="1" /></build>\n"""
		return s
	def write_3mf(self, path):
		#with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED,True,5) as z:
		with zipfile.ZipFile(path,"w",zipfile.ZIP_STORED,True) as z:
			z.writestr('[Content_Types].xml', """<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" /><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" /></Types>\n""")
			z.writestr("_rels/.rels",
"""<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" /></Relationships>\n""")
			z.writestr("3D/3dmodel.model", self.format_3mf_mesh())
	def write_amf(self, path):
		with open(path,"w") as f:
			f.write("""<?xml version="1.0" encoding="UTF-8"?>
<amf unit="millimeter">
<object id="0">
<mesh><vertices>\n""")
			for v in self.v:
				f.write('<vertex><coordinates>')
				for a,b in zip(('x','y','z'),v):
					f.write('<{0}>{1}</{0}>'.format(a,b))
				f.write('</coordinates></vertex>')
			f.write('</vertices>\n<volume>\n')
			for t in self.triangles():
				f.write('<triangle>')
				for i in range(3):
					f.write('<{0}>{1}</{0}>'.format('v'+str(i+1), t[i]))
				f.write('</triangle>')
			f.write("""</volume>
</mesh>
</object>
</amf>\n""")

def main():
	p=ArgumentParser()
	p.add_argument("-i", "--input", nargs=1)
	p.add_argument("-f", "--format", nargs=1, default="auto", help="one of: auto 3mf amf vrml")
	p.add_argument("-o", "--output", nargs=1, default="/dev/null")
	p.add_argument("-r", "--reverse-winding", default=False, action="store_true", help="reverse vertex winding")
	args=p.parse_args()
	me=Mesh()
	with open(args.input[0]) as f:
		me.read_obj(f)
	me.hi()
	if args.reverse_winding:
		me.reverse_winding()
	fmt=args.format[0]
	out=args.output[0]
	if fmt=='auto':
		fmt=out[-3:]
	if fmt=='3mf':
		me.write_3mf(out)
	elif fmt=='amf':
		me.write_amf(out)
	elif fmt=='vrml' or fmt=='wrl':
		me.write_vrml(out)
	else:
		print("Unknown output format: %s." % fmt, "I can write 3mf, amf, vrml")

if __name__=="__main__":
	main()

