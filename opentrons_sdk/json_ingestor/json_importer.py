from collections import OrderedDict
import itertools
import json
import os

from opentrons_sdk import containers
from opentrons_sdk.labware import instruments
from opentrons_sdk.robot import Robot
from opentrons_sdk.util import vector


class JSONCompilerValidationError(Exception):
    pass


class BaseHandler(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self):
        raise NotImplementedError

    def perform(self):
        raise NotImplementedError

    def submit(self):
        self.validate()
        return self.perform()


class JSONPCompiler(BaseHandler):
    def __init__(self, protocol: (str, OrderedDict)):
        super().__init__()
        self._protocol_input = protocol
        self.protocol = self.read_protocol(protocol)

    def get_protocol_from_file(self, path):
        with open(path) as f:
            return json.load(f, object_pairs_hook=OrderedDict)

    def read_protocol(self, protocol):
        if isinstance(protocol, str):
            if os.path.isfile(protocol):
                return self.get_protocol_from_file(protocol)
            return json.loads(protocol, object_pairs_hook=OrderedDict)
        elif isinstance(protocol, OrderedDict):
            return protocol
        raise Exception('Protocol must be a file, json string, or OrderedDict')


    def validate(self):
        errors = []
        warnings = []

        # Process errors
        if 'head' not in self.protocol:
            errors.append('JSON Protocol is missing "HEAD" section')
        if 'deck' not in self.protocol:
            errors.append('JSON Protocol is missing "DECK" section')
        if 'instructions' not in self.protocol:
            errors.append('JSON Protocol is missing "INSTRUCTIONS" section')

        # Process warnings
        if 'ingredients' not in self.protocol:
            warnings.append(
                'JSON Protocol section "Ingredients" will not be used'
            )

        self.warnings.extend(warnings)
        self.errors.extend(errors)

        if errors:
            raise JSONCompilerValidationError('Errors encountered compiling JSON')


    def perform(self):
        pass


    # def interpret_json_protocol(json_protocol: OrderedDict):
    #     robot_deck = interpret_deck(json_protocol['deck'])
    #     robot_head = interpret_head(robot_deck, json_protocol['head'])
    #     interpret_instructions(
    #         robot_deck, robot_head, json_protocol['instructions']
    #     )





# class BaseHandler(object):
#     def validate(self):
#         raise NotImplementedError
#
#     def submit(self):
#         validation_errors = self.validate()
#         if not validation_errors:
#             self.perform()
#
#
#     def perform(self):
#         raise NotImplementedError

def interpret_json_protocol(json_protocol: OrderedDict):
    robot_deck = interpret_deck(json_protocol['deck'])
    robot_head = interpret_head(robot_deck, json_protocol['head'])
    interpret_instructions(
        robot_deck, robot_head, json_protocol['instructions']
    )


def interpret_deck(deck_info: OrderedDict):
    """
    "deck": {
        "p200-rack": {
            "labware": "tiprack-200ul",
            "slot" : "A1"
        },
        ".75 mL Tube Rack": {
            "labware": "tube-rack-.75ml",
            "slot" : "C1"
        },
        "trash": {
            "labware": "point",
            "slot" : "B2"
        }
    }
    :param protocol:
    :param deck_info:
    :return:
    """

    containers_data = {}
    for name, definition in deck_info.items():
        container_type = definition.get('labware')
        slot = definition.get('slot')
        container_obj = containers.load(container_type, slot, name)
        containers_data[name] = {'instance': container_obj}
    return containers_data


def interpret_head(robot_deck, head_dict: OrderedDict):

    """
    res example:
    { name: {
        'instance': ..,
        'settings': {'down-plunger-speed', '
        }
    }

    :param protocol:
    :param head_dict:
    :return:
    """

    SUPPORTED_TOOL_OPTIONS = {
        'tool',
        'tip-racks',
        'trash-container',
        'multi-channel',
        'axis',
        'volume',
        'down-plunger-speed',
        'up-plunger-speed',
        'tip-plunge',
        'extra-pull-volume',
        'extra-pull-delay',
        'distribute-percentage',
        'points'
    }


    head_obj = {}
    robot = Robot.get_instance()

    for tool_name, tool_config in head_dict.items():
        # Validate tool_config keys
        assert SUPPORTED_TOOL_OPTIONS >= set(tool_config.keys())
        tool_config.pop('tool')

        tool_instance = instruments.Pipette(
            name=tool_name,
            axis=tool_config.pop('axis'),
            min_volume=0,
            channels=(8 if tool_config.pop('multi-channel') else 1),
            )
        tool_instance.set_max_volume(tool_config.pop('volume'))

        # robot_containers = robot._deck.containers()
        tip_rack_objs = [
            robot_deck[item['container']]['instance']
            for item in tool_config.pop('tip-racks')
        ]
        tool_config['tip-racks'] = tip_rack_objs

        trash_obj = robot_deck[
            tool_config.pop('trash-container')['container']
        ]['instance']
        tool_config['trash-container'] = trash_obj

        tool_config['points'] = [dict(i) for i in tool_config.pop('points')]

        head_obj[tool_name] = {
            'instance': tool_instance,
            'settings': dict(tool_config)
        }
    return head_obj


def interpret_instructions(robot_deck, robot_head, instructions: list):
    """
    [
		{
			"tool" : "p10",
			"groups" : [
				{
					"transfer" : [
    					{
    						"from" : {
    							"container": "plate",
                                "location": "F1",
                                "touch-tip": false
    						},
    						"to": {
                            	"container" : "plate",
    							"location" : "A12",
    							"tip-offset" : 0,
    							"delay" : 0,
    							"touch-tip" : false
                            },
                            	"volume" : 10
						},
                        {
                            "from" : {
                                "container": "plate",
                                "location": "D1",
                                "touch-tip": false
                            },
                            "to": {
                                "container" : "plate",
                                "location" : "A2",
                                "tip-offset" : 0,
                                "delay" : 0,
                                "touch-tip" : false
                            },
                                "volume" : 10
                        }
					]
    :param robot_deck:
    :param robot_head:
    :param instructions:
    :return:
    """
    for instruction_dict in instructions:
        tool_name = instruction_dict.get('tool')
        tool_obj = robot_head[tool_name]['instance']
        trash_container = robot_head[tool_name]['settings']['trash-container']

        tips = itertools.cycle(
            itertools.chain(*robot_head[tool_name]['settings']['tip-racks'])
        )

        for group in instruction_dict.get('groups'):
            # We always pick up a new tip when entering a group
            tool_obj.pick_up_tip(next(tips))
            for command_type, commands_calls in group.items():
                handler = lambda args: handle_command(
                        tool_obj,robot_deck, robot_head, command_type, args
                    )

                if isinstance(commands_calls, list):
                    [handler(command_arg) for command_arg in commands_calls]

                # Note: Distribute command does not have an array of calls but
                # rather a dict with the distribute call info
                elif isinstance(commands_calls, dict):
                    handler(commands_calls)

            # LEAVING GROUP
            tool_obj.drop_tip(trash_container)


def handle_command(tool_obj, robot_deck, robot_head, command, command_args):
    SUPPORTED_COMMANDS = {
        'transfer': handle_transfer,
        'distribute': handle_distribute,
        'mix': handle_mix,
        'consolidate': handle_consolidate
    }

    if command not in SUPPORTED_COMMANDS:
        raise Exception('Unsupported COMMAND "{}" encountered'.format(command))


    return SUPPORTED_COMMANDS[command](
        tool_obj, robot_deck, robot_head, command_args
    )


def handle_transfer(tool_obj, robot_deck, robot_head, command_args):
    # TODO: validate command args
    volume = command_args.get('volume', tool_obj.max_volume)
    tool_settings = robot_head[tool_obj.name]['settings']
    should_extra_pull = command_args.get('extra-pull', False)

    handle_transfer_from(
        tool_obj,
        tool_settings,
        robot_deck,
        robot_head,
        command_args['from'],
        volume,
        should_extra_pull
    )
    handle_transfer_to(
        tool_obj,
        robot_deck,
        robot_head,
        command_args['to'],
        volume
    )


def handle_transfer_from(
        tool_obj,
        tool_settings,
        robot_deck,
        robot_head,
        from_info,
        volume,
        extra_pull=False
):
    extra_pull_delay = (
        tool_settings.get('extra-pull-delay', 0)
        if extra_pull
        else 0
    )
    extra_pull_volume = (
        tool_settings.get('extra-pull-volume', 0)
        if extra_pull
        else 0
    )

    from_container = robot_deck[from_info['container']]['instance']
    from_well = from_container[from_info['location']]

    should_touch_tip_on_from = from_info.get('touch-tip', False)
    from_tip_offset = from_info.get('tip-offset', 0)
    from_delay = from_info.get('delay', 0)

    from_location = (
        from_well,
        from_well.from_center(x=0, y=0, z=-1) + vector.Vector(0, 0, from_tip_offset)
    )

    tool_obj.aspirate(volume + extra_pull_volume, from_location)
    tool_obj.delay(extra_pull_delay)
    tool_obj.dispense(extra_pull_volume)
    if should_touch_tip_on_from:
        tool_obj.touch_tip()
    tool_obj.delay(from_delay)

def handle_transfer_to(
        tool_obj,
        robot_deck,
        robot_head,
        to_info,
        volume
):
    to_container = robot_deck[to_info['container']]['instance']
    to_well = to_container[to_info['location']]

    should_touch_tip_on_to = to_info.get('touch-tip', False)
    to_tip_offset = to_info.get('tip-offset', 0)
    to_delay = to_info.get('delay', 0)
    blowout = to_info.get('blowout', False)

    to_location = (
        to_well,
        to_well.from_center(x=0, y=0, z=-1) + vector.Vector(0, 0, to_tip_offset)
    )

    tool_obj.dispense(volume, to_location)
    if blowout:
        tool_obj.blow_out(to_location)

    if should_touch_tip_on_to:
        tool_obj.touch_tip()

    if to_delay is not None:
        tool_obj.delay(to_delay)


def handle_distribute(tool_obj, robot_deck, robot_head, command_args):
    # Refactor
    tool_settings = robot_head[tool_obj.name]['settings']

    from_info = command_args['from']
    to_info_list = command_args['to']

    total_to_volume = sum(to_info['volume'] for to_info in to_info_list)
    distribute_percent = tool_settings.get('distribute-percentage', 0)

    from_volume = total_to_volume * (1 + distribute_percent)

    handle_transfer_from(
        tool_obj,
        tool_settings,
        robot_deck,
        robot_head,
        from_info,
        from_volume
    )

    for to_info in to_info_list:
        handle_transfer_to(
            tool_obj,
            robot_deck,
            robot_head,
            to_info,
            to_info['volume']
        )


def handle_mix(tool_obj, robot_deck, robot_head, command_args):
    volume = command_args.get('volume', tool_obj.max_volume)
    well = None

    tool_obj.aspirate(volume, well)
    tool_obj.mix(command_args.get('repetitions', 0))

    if command_args.get('blow-out'):
        tool_obj.robot.move_to_top(well, instrument=tool_obj, create_path=False)
        tool_obj.blow_out()


def handle_consolidate(tool_obj, robot_deck, robot_head, command_args):
    # Refactor
    tool_settings = robot_head[tool_obj.name]['settings']

    from_info_list = command_args['from']
    to_info = command_args['to']

    total_volume = sum(from_info['volume'] for from_info in from_info_list)

    for from_info in from_info_list:
        handle_transfer_from(
            tool_obj,
            tool_settings,
            robot_deck,
            robot_head,
            from_info,
            from_info['volume']
        )

    handle_transfer_to(
        tool_obj,
        robot_deck,
        robot_head,
        to_info,
        total_volume
    )
