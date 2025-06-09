const shoppingCart =(()=>{
    let cartItem = [];
//private
    function addItemCart(item){
        cartItem.push(item);
    }

    function calculatetotal(item){
        total = 0;
        cartItem.forEach(item=>{
            total += item.price
        })
        return total
    }

    return {
        //Public API
        addItme: function(item){
            addItemCart(item)
        console.log(`${item.name} has been added to the cart`)
        },

        checkout: function(item){
            total = calculatetotal(item)
        console.log(`Your total is: R${total.toFixed(2)}`)
        }

    }
})()

shoppingCart.addItme({name: 'Apples', price: 30})
shoppingCart.addItme({name: 'Banana', price: 20})
shoppingCart.addItme({name: 'Grape', price: 50})
shoppingCart.checkout()
