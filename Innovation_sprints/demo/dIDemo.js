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

shoppingCart.addItme({name: 'Apples', price: 30})
shoppingCart.addItme({name: 'Banana', price: 20})
shoppingCart.addItme({name: 'Grape', price: 50})
shoppingCart.checkout()
