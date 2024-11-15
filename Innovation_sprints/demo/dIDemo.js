// CartService - Manages the cart operations
class CartService {
    constructor() {
      this.cartItems = [];
    }
  
    addItem(item) {
      this.cartItems.push(item);
      console.log(`${item.name} has been added to the cart.`);
    }
  
    calculateTotal() {
      let total = 0;
      this.cartItems.forEach(item => {
        total += item.price;
      });
      return total;
    }
  
    getItems() {
      return this.cartItems;
    }
  }
  
  // ShoppingCart - Uses the CartService to perform actions
  const shoppingCart = ((cartService) => {
    // Public API: exposing methods that interact with CartService
    return {
      addItem: function(item) {
        cartService.addItem(item);
      },
  
      checkout: function() {
        const total = cartService.calculateTotal();
        console.log(`Total price: R${total.toFixed(2)}`);
        console.log(`Proceeding to checkout with total: R${total.toFixed(2)}`);
      }
    };
  })(new CartService());  // Injecting the CartService dependency
  
  // Demo usage
  shoppingCart.addItem({ name: 'Apple', price: 1.50 });
  shoppingCart.addItem({ name: 'Banana', price: 0.99 });
  shoppingCart.addItem({ name: 'Orange', price: 2.00 });
  shoppingCart.checkout();
  