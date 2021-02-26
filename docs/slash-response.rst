.. currentmodule:: dislash.interactions

Responding to a slash-command
=============================

.. _interaction:

Interaction
-----------

| Obtainable via **async** functions decorated with ``@slash_client.command()`` or ``@slash_commands.command()``,
| As well as via ``on_slash_command`` event.
| See :ref:`slash_client` and :ref:`examples`

.. autoclass:: Interaction

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at

    .. automethod:: reply

    .. automethod:: edit

    .. automethod:: delete


.. _interaction_data:

Interaction Data
----------------

.. autoclass:: InteractionData

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at



.. _interaction_data_option:

Interaction Data Option
-----------------------

.. autoclass:: InteractionDataOption

    .. automethod:: get

    .. automethod:: get_option

    .. automethod:: option_at
