class Plain:
    def __eq__(self, value: object) -> bool:
        return True


reveal_type(Plain.__hash__)
reveal_type(Plain().__hash__)
s = {Plain()}
d = {Plain(): 1}
hash(Plain())
