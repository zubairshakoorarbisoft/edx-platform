"""
Block Short Label Transformer
"""
from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer
from xmodule.modulestore.django import modulestore
from xmodule.util.misc import get_default_short_labeler


class BlockShortLabelTransformer(BlockStructureTransformer):
    """
    Keep track of the short label of any graded subsections in the block structure.
    """
    READ_VERSION = 1
    WRITE_VERSION = 1

    @classmethod
    def name(cls):
        return "short_label"

    @classmethod
    def collect(cls, block_structure):
        block_structure.request_xblock_fields('format')

    def transform(self, usage_info, block_structure):
        """
        Mutates block_structure adding extra field which contains block's short label, if applicable.
        """
        store = modulestore()
        with store.bulk_operations(usage_info.course_key):
            course = store.get_course(usage_info.course_key, depth=2)
            short_labeler = get_default_short_labeler(course)

            for block_key in block_structure.topological_traversal():
                block_format = block_structure.get_xblock_field(block_key, 'format')
                if block_format:
                    block_structure.set_transformer_block_field(
                        block_key, self, 'short_label', short_labeler(block_format)
                    )
