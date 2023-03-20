


class StateBatchParams:
    def __init__(self, input: bytes):
        self.should_start_at_element = int.from_bytes(input[32:64], byteorder="big")
        self.num_states = int.from_bytes(input[64:96], byteorder="big")

        self.states = []
        offset = 96
        for _ in range(self.num_states):
            self.states.append(input[offset:offset+32])
            offset += 32

    def get_should_start_at_element(self) -> int:
        return self.should_start_at_element

    def get_num_states(self) -> int:
        return self.num_states

    def get_state(self, index: int) -> bytes:
        return self.states[index]