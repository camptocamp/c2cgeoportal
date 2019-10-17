# pylint: disable=no-self-use

from . import AbstractViewsTests


class TestTreeGroup(AbstractViewsTests):
    def check_children(self, form, group, expected):
        form_group = form.html.select_one(".item-{}".format(group))
        items = form_group.select(".deform-seq-item")
        assert len(expected) == len(items)
        for item, exp in zip(items, expected):
            assert exp["label"] == item.select_one(".well").getText().strip()
            for key, value in exp["values"].items():
                assert value == item.select_one('input[name="{}"]'.format(key))["value"]
