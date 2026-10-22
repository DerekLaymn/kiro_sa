# Examples showing the new type_erasure and type_overwriting mutations
# These are seed programs that would be transformed by the LLM generator

# =============================================================================
# EXAMPLE 1: type_erasure - Test inference on generic functions
# =============================================================================

def example_1_original():
    """Original annotated version"""
    from typing import TypeVar, reveal_type
    
    T = TypeVar('T')
    
    def identity(x: T) -> T:
        return x
    
    result = identity([1, 2, 3])
    reveal_type(result)  # Both should infer: list[int]


def example_1_after_type_erasure():
    """After type_erasure mutation - annotations removed"""
    from typing import TypeVar, reveal_type
    
    T = TypeVar('T')
    
    def identity(x):  # ← Annotation removed
        return x      # ← Can checkers infer T?
    
    result = identity([1, 2, 3])
    reveal_type(result)  # mypy: list[int]? ty: list[Unknown]? object?


# =============================================================================
# EXAMPLE 2: type_overwriting - Introduce wrong return type
# =============================================================================

def example_2_original():
    """Original correct version"""
    from typing import reveal_type
    
    def get_config() -> dict[str, bool]:
        return {"debug": True, "verbose": False}
    
    config = get_config()
    print(config["debug"])  # OK


def example_2_after_type_overwriting():
    """After type_overwriting mutation - return type is a lie"""
    from typing import reveal_type
    
    def get_config() -> list[str]:  # ← LIE! Actually returns dict
        return {"debug": True, "verbose": False}  # Returns dict, not list
    
    config = get_config()
    reveal_type(config)  # Does checker believe the lie? list[str]?
    
    # Runtime witness - this will crash!
    try:
        config.append("new")  # list method on dict
        print("Checker accepted the lie!")
    except AttributeError as e:
        print(f"Runtime caught it: {e}")


# =============================================================================
# EXAMPLE 3: type_erasure on parameters only
# =============================================================================

def example_3_original():
    """Original with parameter annotations"""
    from typing import reveal_type
    
    def process(items: list[int], multiplier: int) -> int:
        total: int = sum(items)
        return total * multiplier
    
    result = process([1, 2, 3], 10)
    reveal_type(result)  # int


def example_3_after_partial_erasure():
    """After type_erasure on parameters - return type kept"""
    from typing import reveal_type
    
    def process(items, multiplier) -> int:  # ← Parameters erased
        total = sum(items)  # ← Local variable erased
        return total * multiplier
    
    result = process([1, 2, 3], 10)
    reveal_type(result)  # Still int? Or Unknown?


# =============================================================================
# EXAMPLE 4: type_overwriting with variance
# =============================================================================

def example_4_original():
    """Original with covariant generic"""
    from typing import TypeVar, Generic, reveal_type
    
    T = TypeVar('T')
    
    class Box(Generic[T]):
        def __init__(self, value: T) -> None:
            self.value = value
        
        def get(self) -> T:
            return self.value
    
    box: Box[int] = Box(42)
    reveal_type(box.get())  # int


def example_4_after_type_overwriting():
    """After type_overwriting - change generic parameter"""
    from typing import TypeVar, Generic, reveal_type
    
    T = TypeVar('T')
    
    class Box(Generic[T]):
        def __init__(self, value: T) -> None:
            self.value = value
        
        def get(self) -> T:
            return self.value
    
    box: Box[str] = Box(42)  # ← LIE! Box[str] but value is int
    reveal_type(box.get())  # Does checker say str? int? T?
    
    # Runtime witness
    result = box.get()
    try:
        result.upper()  # str method on int
        print("Checker accepted incompatible type!")
    except AttributeError as e:
        print(f"Runtime caught it: {e}")


# =============================================================================
# EXAMPLE 5: type_erasure on class attributes
# =============================================================================

def example_5_original():
    """Original with typed class"""
    from typing import reveal_type
    
    class Point:
        x: int
        y: int
        
        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y
    
    p = Point(10, 20)
    reveal_type(p.x)  # int


def example_5_after_type_erasure():
    """After type_erasure on class - remove attribute annotations"""
    from typing import reveal_type
    
    class Point:
        # x: int  ← Erased
        # y: int  ← Erased
        
        def __init__(self, x, y):  # ← Parameters erased
            self.x = x
            self.y = y
    
    p = Point(10, 20)
    reveal_type(p.x)  # Can checkers infer int? Or Unknown?


# =============================================================================
# EXAMPLE 6: Combined - type_overwriting then type_erasure
# =============================================================================

def example_6_mutation_sequence():
    """Multiple mutations can be applied in sequence"""
    from typing import reveal_type
    
    # Step 1: type_overwriting - wrong return type
    def calculate() -> str:  # Says str, returns int
        return 42
    
    # Step 2: type_erasure - remove parameter types
    def use_result(x):  # Was: x: int
        reveal_type(x)
        return x * 2
    
    result1 = calculate()  # Checker thinks str
    result2 = use_result(result1)  # Passes str to function expecting int?
    reveal_type(result2)  # What does checker say?
    
    # Runtime witness
    print(result2)  # Will this work?


if __name__ == "__main__":
    print("These are example mutations - not meant to be run directly")
    print("The LLM generator will create similar programs based on mutation operators")
