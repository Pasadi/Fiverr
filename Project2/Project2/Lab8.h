//Print your Name, Section Name and ID
#ifndef H_StackType
#define H_StackType

#include <iostream>
#include <cassert>

using namespace std;
template <class Type>
class stackType
{

public:
	const stackType<Type>& operator=(const stackType<Type>&);
	void initializeStack();
	bool isEmptyStack() const;
	bool isFullStack() const;
	void push(const Type& newItem);
	Type top() const;
	void pop();
	stackType(int stackSize = 100);
	stackType(const stackType<Type>& otherStack); 
	~stackType();

private:
	 //Declare three private valuables for the class stackType 
	//a. Declare a valuable named maxStackSize type of int 
	//b. Declare a valuable named stackTop type of int
    //c.Declare a pointer named list to the array that holds the stack element
	int maxStackSize;
	int stackTop;
	Type *list;

	void copyStack(const stackType<Type>& otherStack);

};

template <class Type>
void stackType<Type>::initializeStack()
{
	stackTop = 0;
}//end initializeStack
 
 
template <class Type>
bool stackType<Type>::isFullStack() const
{
	return (stackTop == maxStackSize);
} //end isFullStack


// Implement isEmptyStack operation
/*Purpose:
* Check if stack has no elements
* Return:
* true - if stack has no elements
* false - if stack has elements
*/
template <class Type>
bool stackType<Type>::isEmptyStack() const
{
	return (stackTop == 0); // The stack is considered empty when the indicator that points to the top of the stack is = 0
} //end isEmptyStack

template <class Type>
void stackType<Type>::push(const Type& newItem)
{
	if (!isFullStack())
	{
		list[stackTop] = newItem; //add newItem to the
								  //top of the stack
		stackTop++; //increment stackTop
	}

	else
		cout << "Cannot add to a full stack." << endl;
}//end push

template <class Type>
Type stackType<Type>::top() const
{
	assert(stackTop != 0); //if stack is empty, terminate the program
	return list[stackTop - 1]; //return the element of the stack indicated by stackTop - 1
}

//Implement pop() operation
/* Purpose :
* Reduce the size of the stack by one given that the stack has elements
*/
template<class Type>
inline void stackType<Type>::pop()
{
	if (!isEmptyStack()) 
	{
		stackTop--;
	}
	else
		cout << "pop - Empty Stack" << endl;
}
//end pop
 
template <class Type>
stackType<Type>::stackType(int stackSize)
{
	if (stackSize <= 0)
	{
		cout << "Size of the array to hold the stack must be positive." << endl;
		cout << "Creating an array of size 100." << endl; 
		maxStackSize = 100;
	}
	else
		maxStackSize = stackSize; //set the stack size to the value specified by the parameter stack size

	stackTop = 0; //set stackTop to 0
	list = new Type[maxStackSize]; //create the array to hold the stack elements

}//end constructor

 //Implement Destructor operation
/*
* Purpose:
* Delete objects that were dynamically created using 'new / new[]' to avoid memory leaks
*
*/
template <class Type>
stackType<Type>::~stackType()
{
	delete[] list;
	list = NULL;
}


template <class Type>
void stackType<Type>::copyStack(const stackType<Type>& otherStack)
{
	delete[] list;
	maxStackSize = otherStack.maxStackSize;
	stackTop = otherStack.stackTop;
	list = new Type[maxStackSize];
	//copy otherStack into this stack

	for (int j = 0; j < stackTop; j++)
		list[j] = otherStack.list[j];
} //end copyStack


template <class Type>
stackType<Type>::stackType(const stackType<Type>& otherStack)
{
	list = nullptr;
	copyStack(otherStack);
}//end copy constructor


template <class Type>
const stackType<Type>& stackType<Type>::operator= (const stackType<Type>& otherStack) 
{	
	if (this != &otherStack) //avoid self-copy
		copyStack(otherStack);
	return *this;
} //end operator
#endif