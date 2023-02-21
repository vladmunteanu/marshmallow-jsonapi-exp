from marshmallow import Schema, fields


class LinksSchema(Schema):
    self = fields.String()
    related = fields.String()


def generate_url(link, **kwargs):
    return link.format_map(kwargs) if link else None
