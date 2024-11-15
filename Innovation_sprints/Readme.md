## Innovation sprint project Software Design Patterns

# JavaScript design patterns

Design patterns are reusable templates that capture best practices for addressing common software design challenges. They provide a systematic approach to software design, fostering modularity, flexibility, and maintainability in code.

**Types of design patterns**

1. **Creational** - Creational patterns center on object creation methods, offering flexible and controlled approaches for instantiating objects.

- Singleton - The Singleton Pattern guarantees that a class has a single instance and offers a global access point to that instance.
- Factory - The Factory Pattern enables object creation without defining specific classes, encapsulating the creation logic in a separate factory method. This allows for flexibility and decouples the creator from the objects it creates.
- Constructor - The Constructor Pattern creates objects using a constructor function with the `new` keyword, allowing object properties to be defined and initialized within the constructor function.
- Prototype - The Prototype pattern in JavaScript centers on creating objects by cloning or extending existing prototype objects. This approach enables the creation of new instances without explicitly defining their classes.
- Builder - This type of pattern, builder class or object is tasked with constructing the final object. It offers a series of methods to configure and set the properties of the object under construction.
- Module - The Module Pattern groups related methods and properties into a single module, offering a clean structure for organizing and safeguarding code. It supports private and public members, promoting information hiding and reducing global namespace pollution.

***Inversion of control (IoC)***

Inversion of control (IoC) - is a principle (not a design pattern) focusing on inverting the control flow of a program. Inversion of control (IoC) techniques give developers a way to break out of traditional programming flow, and it offers them more flexibility and greater control over their code.
- The design patterns which are used to implement IoC in object-oriented programming includes:
   - Dependency injection - is a software design pattern where an object or function makes use of other objects or functions (dependencies) without worrying about their underlying implementation details.

**Module pattern example**:
- Private Data: cartItems and the functions addToCart and calculateTotal are encapsulated within the module, preventing direct access from the outside.
- Public API: addItem and checkout are exposed to interact with the cart.
- Encapsulation: Internal logic is hidden from the global scope, ensuring a clean namespace.

**Dependency Injection example**:

**Benefits of Dependency Injection in this case**:
- **Decoupling**: shoppingCart is decoupled from the specific implementation of the cart logic. It no longer directly manages the cart state but relies on the CartService.
**Testability**: It's easier to mock or replace the CartService for testing purposes. You can inject a mock version of CartService to simulate different behaviors without changing the shoppingCart module.
**Flexibility**: If you need to replace CartService with another service that provides more advanced cart features, you can do so without modifying shoppingCart.


2. **Structural** - Structural patterns are concerned with organizing and combining objects to create larger, cohesive structures. They define relationships between objects and offer flexible methods for managing and modifying these structures.

- Decorator Pattern
- Facade Pattern
- Adapter
- Bridge
- Composite


3. **Behavioral** - Behavioral patterns emphasize interactions between objects and the allocation of responsibilities. They offer solutions for effective communication, coordination, and collaboration among objects.

- Observer Pattern
- Strategy Pattern
- Command Pattern
- Iterator Pattern
- Mediator Pattern


