const shoppingCart = (() => {
    let cartItems = [];
  
    // Private function to add item to the cart
    function addToCart(item) {
      cartItems.push(item);
      console.log(`${item.name} has been added to the cart.`);
    }
  
    // Private function to calculate the total price of items in the cart
    function calculateTotal() {
      let total = 0;
      cartItems.forEach(item => {
        total += item.price;
      });
      console.log(`Total price: R${total.toFixed(2)}`);
      return total;
    }
  
    // Public API: returning methods to interact with the cart
    return {
      // Public method to add an item
      addItem: function(item) {
        addToCart(item);
      },
  
      // Public method to checkout
      checkout: function() {
        const total = calculateTotal();
        console.log(`Proceeding to checkout with total: R${total.toFixed(2)}`);
      }
    };
  })();
  
  // Demo
  shoppingCart.addItem({ name: 'Apple', price: 4.50 });
  shoppingCart.addItem({ name: 'Banana', price: 3.99 });
  shoppingCart.addItem({ name: 'Orange', price: 3.00 });
  shoppingCart.checkout();
  