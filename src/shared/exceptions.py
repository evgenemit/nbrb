from shared.models.trade import TradeStatus


class TradeStatusAlreadySet(Exception):
    def __init__(self, status: TradeStatus) -> None:
        msg = (
            'Cannot change status of trade because '
            f'it is already set ({status.value})'
        )
        super().__init__(msg)
