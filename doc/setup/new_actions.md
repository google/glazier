# Creating New Actions

Glazier's Actions are the core of the system's configuration language. Glazier
ships with some [existing actions](../../glazier/lib/actions/README.md), but for more
custom functionality, you can also create your own.

Actions are defined in the [glazier/lib/actions/ module](../../glazier/lib/actions/).

## BaseAction

All actions extend from the BaseAction class, which provides some core
underlying functionality common to all actions. BaseAction is defined in
[base.py](../../glazier/lib/actions/base.py).

All actions receive two parameters, as defined by BaseAction: `args` and
`build_info`.

*   `args` is the data received from the configuration file. It can be any data
    type supported by YAML.

    *   An example of the Get action with its args, as written in a config:

            Get:
                - ['windows10.wim', 'c:\base.wim', '4b5b6bf0e59dadb4663ad9b4110bf0794ba24c344291f30d47467d177feb4776']

*   `build_info` is the internal state of the installer. This is automatically
    passed by the config handler while the configs are being parsed.

## Action Definition

Within the *glazier/lib/actions* module there are several libraries. You can extend one
of the existing libraries or create a new one. The layout is strictly
organizational.

In this example, we'll create the action `FancyAction` to be used in our imaging
configs.

Import `BaseAction` and create a new Python class decended from it. The name of
the class will be the name of the command we use in new configs.

    from glazier.lib.actions.base import ActionError
    from glazier.lib.actions.base import BaseAction

    class FancyAction(BaseAction):
      """Do awesome things."""

      def Run(self):
        my_arg = self._args[0]
        try:
          DoFancyStuff(my_arg)
        except NotFancyEnough:
          raise ActionError("Problem running FancyAction with %s" % my_arg)

The class must declare at least one function, called `Run`. Run is called
whenever Autobuild intends to execute the action. You can add any additional
supporting functions you like to the class, as long as `Run` exists as the
entrypoint. In this case, we pass the args to the `DoFancyStuff` function (not
shown), for some additional processing.

Note that your class will have access to the config arguments via the
*self.\_args* variable. This will be automatically populated, and you can
reference it anywhere within the class that you need.

`ActionError` should be thrown any time your class encounters an error and
cannot complete cleanly. This signals Autobuild that the action has failed, and
it should abort the installation until things are fixed.

Once your action class has been defined, open *glazier/lib/actions/\_\_init\_\_.py*. Add
a new line declaring the name of your class to export it to the config handler.

    FancyAction = fancy.FancyAction

That's it! You can now use `FancyAction` in your Glazier configs.

## Validation

`BaseAction` classes include a second reserved function, `Validate`. Defining
this function in your classes is optional, but recommended.

When `Validate` is called on an action, the *self.\_args* variable is
interrogated for correctness. For example, the action `Get` expects to receive a
list with a fixed number of parameters. If Get is passed something other than a
list, we know a mistake has been made and the config is broken.

An example validator for Get:

      def Validate(self):
        self._TypeValidator(self._args, list)
        for arg in self._args:
          self._ListOfStringsValidator(arg, 2, 3)

The `Validate` function should raise `ValidationError` if it finds a problem
with *self.\_args*.

### Config Testing

We can use the `Validate` function to implement presubmit or continuous build
testing of our configs.

In this example, we'll assume we have a Python script which will load each
config file using the yaml module.

Once we have the config YAML, testing validity of the entire config is as simple
as looping through each element, verifying that a corresponding Action exists,
and calling its `Validate` function.

    from glazier.lib import actions

    ...
    # config = loaded config file content
    ...

    for c in config:
      if c in dir(actions):
        act_obj = getattr(actions, str(c))
        a = act_obj(args=config[c], build_info=None)
        try:
          a.Validate()
        except actions.ValidationError as e:
          self.fail(e)  # broken config
