from dataclasses import dataclass, asdict, field
from ipaddress import IPv4Address
import json

@dataclass
class Tag:
	ip: IPv4Address = field(default_factory=IPv4Address)
	isp: str = field(default_factory=str)
	city: str = field(default_factory=str)
	country: str = field(default_factory=str)
	coordinates: tuple[float, float] = ()
	hops: int = 1
	is_alive: bool = False
	trace: list = field(default_factory=list)

	def as_json(self):
		return json.dumps(asdict(self), indent=2)

	@staticmethod
	def from_dict(data):
		t = Tag(**data)
		trace = [Tag.from_dict(tra) for tra in t.trace]
		return Tag(
			t.ip,
			t.isp,
			t.city,
			t.country,
			t.coordinates,
			t.hops,
			t.is_alive,
			trace
			)


	@staticmethod
	def from_json(data):
		d = json.loads(data)
		return Tag(**d)

	def __str__(self):
		return '''
ip: {}
isp: {}
city: {}
country: {}
coordinates: {}
hops: {}
is_alive: {}
trace: {}
		'''.format(*[v for v in asdict(self).values()])


if __name__ == '__main__':
	print(Tag("93.210.156.26"))
