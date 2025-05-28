import asyncio
import time

from iot.devices import HueLightDevice, SmartSpeakerDevice, SmartToiletDevice
from iot.message import Message, MessageType
from iot.service import IOTService, run_sequence, run_parallel


async def main() -> None:
    # create an IOT service
    service = IOTService()

    # create and register a few devices
    hue_light = HueLightDevice()
    speaker = SmartSpeakerDevice()
    toilet = SmartToiletDevice()
    hue_light_id, speaker_id, toilet_id = await asyncio.gather(
        service.register_device(hue_light),
        service.register_device(speaker),
        service.register_device(toilet)
    )

    # # create a few programs
    # wake_up_program = [
    #     Message(hue_light_id, MessageType.SWITCH_ON),
    #     Message(speaker_id, MessageType.SWITCH_ON),
    #     Message(speaker_id, MessageType.PLAY_SONG, "Rick Astley - Never Gonna Give You Up"),
    # ]

    await run_sequence(
        # 1. Turn on devices and change light color in parallel
        run_parallel(
            service.send_msg(Message(hue_light_id, MessageType.SWITCH_ON)),
            service.send_msg(Message(speaker_id, MessageType.SWITCH_ON)),
            service.send_msg(Message(hue_light_id, MessageType.CHANGE_COLOR, "warm white")), # New action
        ),
        # 2. After speaker is on, play song
        service.send_msg(Message(speaker_id, MessageType.PLAY_SONG, "Rick Astley - Never Gonna Give You Up")), # Using PLAY_SONG
        # 3. Open toilet lid after it's on (assuming implicit power-on from connect)
        service.send_msg(Message(toilet_id, MessageType.OPEN)), # New action
    )

    # sleep_program = [
    #     Message(hue_light_id, MessageType.SWITCH_OFF),
    #     Message(speaker_id, MessageType.SWITCH_OFF),
    #     Message(toilet_id, MessageType.FLUSH),
    #     Message(toilet_id, MessageType.CLEAN),
    # ]
    # await asyncio.gather(
    #     service.run_program(wake_up_program),
    #     service.run_program(sleep_program)
    # )
    # run the programs
    await run_parallel(
        # 1. Toilet operations: flush then clean (sequential).
        run_sequence(
            service.send_msg(Message(toilet_id, MessageType.FLUSH)),
            service.send_msg(Message(toilet_id, MessageType.CLEAN)),
            service.send_msg(Message(toilet_id, MessageType.CLOSE)), # New action: close lid after use
        ),
        # 2. Turn off Hue Light and Smart Speaker in parallel.
        run_parallel(
            service.send_msg(Message(hue_light_id, MessageType.SWITCH_OFF)),
            service.send_msg(Message(speaker_id, MessageType.SWITCH_OFF)),
        )
    )


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main())
    end = time.perf_counter()

    print("Elapsed:", end - start)
